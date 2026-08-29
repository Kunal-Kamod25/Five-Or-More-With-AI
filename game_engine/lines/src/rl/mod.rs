pub mod environment;
pub mod random_agent;

pub use environment::{EnvironmentConfig, GameState, Move, StepResult};
pub use random_agent::{evaluate_random_agent, EpisodeStats, EvaluationStats, RandomAgent};
