CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE projects (
    project_id uuid DEFAULT uuid_generate_v4(),
    project_name VARCHAR NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id)
);

CREATE TABLE experiments (
    experiment_id uuid DEFAULT uuid_generate_v4(),
    project_id uuid NOT NULL,
    experiment_name VARCHAR NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (experiment_id),
    CONSTRAINT fk_project
      FOREIGN KEY(project_id) 
        REFERENCES projects(project_id)
        ON DELETE CASCADE
);

CREATE TABLE runs (
    run_id uuid DEFAULT uuid_generate_v4(),
    experiment_id uuid NOT NULL,
    run_name VARCHAR,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id),
    CONSTRAINT fk_experiment
      FOREIGN KEY(experiment_id) 
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE
);

CREATE TABLE logs (
    log_id uuid DEFAULT uuid_generate_v4(),
    experiment_id uuid NOT NULL,
    run_id uuid NOT NULL,
    log_data jsonb NOT NULL,
    checkpoint_path VARCHAR,
    binary_data BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    CONSTRAINT fk_experiment
      FOREIGN KEY(experiment_id) 
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_run
      FOREIGN KEY(run_id) 
        REFERENCES runs(run_id)
        ON DELETE CASCADE
);
