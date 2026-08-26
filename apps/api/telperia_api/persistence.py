from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import uuid4

from telperia_api.ingestion_service import StoredIngestionRecord


class SQLiteIngestionStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def get_by_run_id(self, run_id: str) -> StoredIngestionRecord | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                select
                  result_uploads.id,
                  result_uploads.user_id,
                  result_uploads.run_id,
                  result_uploads.package_sha256,
                  result_uploads.storage_path,
                  raw_result_packages.package_json,
                  result_uploads.visibility,
                  result_uploads.validation_warnings
                from result_uploads
                join raw_result_packages on raw_result_packages.upload_id = result_uploads.id
                where result_uploads.run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if row is None:
                return None

            summary = self.summary_row_for_run(run_id)
            return StoredIngestionRecord(
                upload_id=row["id"],
                user_id=row["user_id"],
                run_id=row["run_id"],
                package_hash=row["package_sha256"],
                storage_path=row["storage_path"],
                raw_package=json.loads(row["package_json"]),
                observatory_summary=summary,
                visibility=_request_visibility(row["visibility"]),
                validation_warnings=json.loads(row["validation_warnings"]),
            )

    def save(self, record: StoredIngestionRecord) -> None:
        package = record.raw_package
        model = package["model"]
        runtime = package["runtime"]
        hardware = package["hardware"]
        environment = package["run_environment"]
        evaluation = package["evaluation"]
        scores = evaluation["scores"]
        factual = scores["factual_reliability_v0_1"]
        ipw = scores["ipw_v0_1"]
        energy = package["energy"]
        confidence = energy.get("energy_confidence")
        public_requested = record.visibility == "submit_for_public_review"
        stored_visibility = "submitted_for_public_review" if public_requested else "private"

        with closing(self._connect()) as connection:
            try:
                connection.execute("begin")
                model_config_id = self._upsert_model_config(connection, model, runtime)
                hardware_profile_id = self._upsert_hardware_profile(connection, hardware, environment)

                connection.execute(
                    """
                    insert into result_uploads (
                      id, user_id, storage_path, package_sha256, run_id, schema_version,
                      methodology_version, evaluation_suite, visibility, ingestion_status,
                      validation_warnings, public_submission_requested
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, 'accepted', ?, ?)
                    """,
                    (
                        record.upload_id,
                        record.user_id,
                        record.storage_path,
                        record.package_hash,
                        record.run_id,
                        package["schema_version"],
                        package["methodology"]["version"],
                        evaluation["suite"],
                        stored_visibility,
                        json.dumps(record.validation_warnings, sort_keys=True),
                        int(public_requested),
                    ),
                )
                connection.execute(
                    """
                    insert into raw_result_packages (upload_id, storage_path, package_json)
                    values (?, ?, ?)
                    """,
                    (
                        record.upload_id,
                        record.storage_path,
                        json.dumps(package, sort_keys=True, separators=(",", ":")),
                    ),
                )

                evaluation_run_id = str(uuid4())
                connection.execute(
                    """
                    insert into evaluation_runs (
                      id, upload_id, model_config_id, hardware_profile_id, run_id,
                      result_timestamp, node_id, schema_version, methodology_version,
                      evaluation_suite, completed_tasks, total_tasks, completion_ratio,
                      error_count, verification_level, runner_version, is_public
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        evaluation_run_id,
                        record.upload_id,
                        model_config_id,
                        hardware_profile_id,
                        record.run_id,
                        package["timestamp"],
                        environment["node_id"],
                        package["schema_version"],
                        package["methodology"]["version"],
                        evaluation["suite"],
                        evaluation["completed_tasks"],
                        evaluation["total_tasks"],
                        evaluation.get("completion_ratio", 0.0),
                        package["performance"]["error_count"],
                        package["verification"]["level"],
                        package["verification"]["runner_version"],
                    ),
                )
                connection.execute(
                    """
                    insert into run_scores (
                      evaluation_run_id, tci_v0_1, factual_correct_responses,
                      factual_incorrect_responses, factual_abstentions,
                      factual_total_questions, factual_correctness_rate,
                      factual_incorrect_answer_rate, factual_abstention_rate,
                      factual_attempted_accuracy, local_ipw_unscaled,
                      local_ipw_displayed, local_ipw_status, gpu_energy_wh,
                      average_power_w, peak_power_w, sampling_interval_ms,
                      energy_source, energy_scope, energy_confidence,
                      energy_warning_codes, tokens_per_second
                    )
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evaluation_run_id,
                        scores["tci_v0_1"]["final_score"],
                        factual["correct_responses"],
                        factual["incorrect_responses"],
                        factual["abstentions"],
                        factual["total_questions"],
                        factual["correctness_rate"],
                        factual["incorrect_answer_rate"],
                        factual["abstention_rate"],
                        factual["attempted_accuracy"],
                        ipw.get("unscaled"),
                        ipw.get("displayed"),
                        "calculated" if "unscaled" in ipw else ipw["status"],
                        energy["gpu_energy_wh"],
                        energy["average_power_w"],
                        energy["peak_power_w"],
                        energy["sampling_interval_ms"],
                        energy.get("energy_source", ipw["energy_source"]),
                        energy.get("energy_scope", ipw["energy_scope"]),
                        confidence["quality"] if confidence else None,
                        json.dumps(confidence["warning_codes"] if confidence else [], sort_keys=True),
                        package["performance"]["tokens_per_second"],
                    ),
                )
                if public_requested:
                    connection.execute(
                        """
                        insert into public_submissions (id, evaluation_run_id, submitted_by, status)
                        values (?, ?, ?, 'pending_review')
                        """,
                        (str(uuid4()), evaluation_run_id, record.user_id),
                    )
                connection.commit()
            except sqlite3.Error:
                connection.rollback()
                raise

    def raw_package_for_upload(self, upload_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "select package_json from raw_result_packages where upload_id = ?",
                (upload_id,),
            ).fetchone()
            return json.loads(row["package_json"]) if row is not None else None

    def upload_row_for_run(self, run_id: str) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute("select * from result_uploads where run_id = ?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            return dict(row)

    def summary_row_for_run(self, run_id: str) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                select
                  evaluation_runs.id as result_id,
                  evaluation_runs.run_id,
                  model_configs.model_name,
                  model_configs.model_revision,
                  model_configs.quantization,
                  model_configs.runtime_engine,
                  model_configs.runtime_version,
                  hardware_profiles.gpu,
                  hardware_profiles.gpu_count,
                  hardware_profiles.operating_system,
                  hardware_profiles.monitor_backend,
                  run_scores.tci_v0_1,
                  run_scores.factual_correctness_rate,
                  run_scores.factual_incorrect_answer_rate,
                  run_scores.factual_abstention_rate,
                  run_scores.factual_attempted_accuracy,
                  run_scores.local_ipw_unscaled,
                  run_scores.local_ipw_displayed,
                  run_scores.local_ipw_status,
                  run_scores.gpu_energy_wh,
                  run_scores.energy_confidence,
                  run_scores.energy_warning_codes,
                  evaluation_runs.verification_level,
                  evaluation_runs.methodology_version,
                  evaluation_runs.evaluation_suite,
                  evaluation_runs.completed_tasks,
                  evaluation_runs.total_tasks,
                  evaluation_runs.completion_ratio,
                  evaluation_runs.error_count,
                  evaluation_runs.result_timestamp,
                  evaluation_runs.created_at as published_at
                from evaluation_runs
                join model_configs on model_configs.id = evaluation_runs.model_config_id
                join hardware_profiles on hardware_profiles.id = evaluation_runs.hardware_profile_id
                join run_scores on run_scores.evaluation_run_id = evaluation_runs.id
                where evaluation_runs.run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if row is None:
                raise KeyError(run_id)

            summary = dict(row)
            summary["hardware_label"] = (
                f"{summary['gpu']} / {summary['operating_system']} / {summary['monitor_backend'].upper()}"
            )
            summary["energy_warning_codes"] = json.loads(summary["energy_warning_codes"])
            return summary

    def table_count(self, table_name: str) -> int:
        if table_name not in _TABLE_NAMES:
            raise ValueError("Unknown table name.")
        with closing(self._connect()) as connection:
            return int(connection.execute(f"select count(*) from {table_name}").fetchone()[0])

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(_SCHEMA_SQL)
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("pragma foreign_keys = on")
        return connection

    def _upsert_model_config(
        self,
        connection: sqlite3.Connection,
        model: dict[str, Any],
        runtime: dict[str, Any],
    ) -> str:
        row = connection.execute(
            """
            select id from model_configs
            where model_name = ? and model_revision = ? and quantization = ?
              and runtime_engine = ? and runtime_version = ?
            """,
            (
                model["name"],
                model["revision"],
                model["quantization"],
                runtime["engine"],
                runtime["engine_version"],
            ),
        ).fetchone()
        if row is not None:
            return row["id"]

        model_config_id = str(uuid4())
        connection.execute(
            """
            insert into model_configs (
              id, model_name, model_revision, quantization, runtime_engine, runtime_version
            )
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                model_config_id,
                model["name"],
                model["revision"],
                model["quantization"],
                runtime["engine"],
                runtime["engine_version"],
            ),
        )
        return model_config_id

    def _upsert_hardware_profile(
        self,
        connection: sqlite3.Connection,
        hardware: dict[str, Any],
        environment: dict[str, Any],
    ) -> str:
        row = connection.execute(
            """
            select id from hardware_profiles
            where gpu = ? and gpu_count = ? and driver = ? and cuda = ?
              and system_ram_gb = ? and operating_system = ? and monitor_backend = ?
            """,
            (
                hardware["gpu"],
                hardware["gpu_count"],
                hardware["driver"],
                hardware["cuda"],
                hardware["system_ram_gb"],
                environment["operating_system"],
                environment["monitor_backend"],
            ),
        ).fetchone()
        if row is not None:
            return row["id"]

        hardware_profile_id = str(uuid4())
        connection.execute(
            """
            insert into hardware_profiles (
              id, gpu, gpu_count, driver, cuda, system_ram_gb, operating_system, monitor_backend
            )
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hardware_profile_id,
                hardware["gpu"],
                hardware["gpu_count"],
                hardware["driver"],
                hardware["cuda"],
                hardware["system_ram_gb"],
                environment["operating_system"],
                environment["monitor_backend"],
            ),
        )
        return hardware_profile_id


def _request_visibility(stored_visibility: str) -> str:
    if stored_visibility == "submitted_for_public_review":
        return "submit_for_public_review"
    return stored_visibility


_TABLE_NAMES = {
    "raw_result_packages",
    "result_uploads",
    "model_configs",
    "hardware_profiles",
    "evaluation_runs",
    "run_scores",
    "public_submissions",
}


_SCHEMA_SQL = """
create table if not exists result_uploads (
  id text primary key,
  user_id text not null,
  storage_path text not null unique,
  package_sha256 text not null,
  run_id text not null unique,
  schema_version text not null,
  methodology_version text not null,
  evaluation_suite text not null,
  visibility text not null check (visibility in ('private', 'submitted_for_public_review')),
  ingestion_status text not null check (ingestion_status = 'accepted'),
  validation_warnings text not null,
  public_submission_requested integer not null check (public_submission_requested in (0, 1)),
  created_at text not null default (datetime('now')),
  updated_at text not null default (datetime('now'))
);

create table if not exists raw_result_packages (
  upload_id text primary key references result_uploads(id) on delete cascade,
  storage_path text not null,
  package_json text not null
);

create table if not exists model_configs (
  id text primary key,
  model_name text not null,
  model_revision text not null,
  quantization text not null,
  runtime_engine text not null,
  runtime_version text not null,
  created_at text not null default (datetime('now')),
  unique (model_name, model_revision, quantization, runtime_engine, runtime_version)
);

create table if not exists hardware_profiles (
  id text primary key,
  gpu text not null,
  gpu_count integer not null,
  driver text not null,
  cuda text not null,
  system_ram_gb real not null,
  operating_system text not null,
  monitor_backend text not null,
  created_at text not null default (datetime('now')),
  unique (gpu, gpu_count, driver, cuda, system_ram_gb, operating_system, monitor_backend)
);

create table if not exists evaluation_runs (
  id text primary key,
  upload_id text not null references result_uploads(id) on delete cascade,
  model_config_id text not null references model_configs(id),
  hardware_profile_id text not null references hardware_profiles(id),
  run_id text not null unique,
  result_timestamp text not null,
  node_id text not null,
  schema_version text not null,
  methodology_version text not null,
  evaluation_suite text not null,
  completed_tasks integer not null,
  total_tasks integer not null,
  completion_ratio real not null,
  error_count integer not null,
  verification_level integer not null,
  runner_version text not null,
  is_public integer not null default 0,
  created_at text not null default (datetime('now'))
);

create table if not exists run_scores (
  evaluation_run_id text primary key references evaluation_runs(id) on delete cascade,
  tci_v0_1 real not null,
  factual_correct_responses integer not null,
  factual_incorrect_responses integer not null,
  factual_abstentions integer not null,
  factual_total_questions integer not null,
  factual_correctness_rate real not null,
  factual_incorrect_answer_rate real not null,
  factual_abstention_rate real not null,
  factual_attempted_accuracy real not null,
  local_ipw_unscaled real,
  local_ipw_displayed real,
  local_ipw_status text not null,
  gpu_energy_wh real not null,
  average_power_w real not null,
  peak_power_w real not null,
  sampling_interval_ms integer not null,
  energy_source text not null,
  energy_scope text not null,
  energy_confidence text,
  energy_warning_codes text not null,
  tokens_per_second real not null,
  created_at text not null default (datetime('now'))
);

create table if not exists public_submissions (
  id text primary key,
  evaluation_run_id text not null unique references evaluation_runs(id) on delete cascade,
  submitted_by text not null,
  status text not null check (status = 'pending_review'),
  review_notes text,
  created_at text not null default (datetime('now')),
  reviewed_at text
);
"""
