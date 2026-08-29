use std::time::{Duration, Instant};

use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};

use crate::constants::{GRID_HEIGHT, GRID_WIDTH, MAX_PIECES};

use super::{EnvironmentConfig, GameState, Move};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct EpisodeStats {
    pub score: i32,
    pub total_reward: f32,
    pub steps: usize,
    pub terminated: bool,
    pub truncated: bool,
}

#[derive(Clone, Debug, PartialEq)]
pub struct EvaluationStats {
    pub episodes: usize,
    pub total_steps: usize,
    pub total_score: i64,
    pub highest_score: i32,
    pub lowest_score: i32,
    pub total_reward: f64,
    pub highest_total_reward: f32,
    pub lowest_total_reward: f32,
    pub longest_episode: usize,
    pub shortest_episode: usize,
    pub game_over_episodes: usize,
    pub truncated_episodes: usize,
    pub simulation_time: Duration,
}

impl EvaluationStats {
    pub fn average_score(&self) -> f64 {
        self.total_score as f64 / self.episodes as f64
    }

    pub fn average_episode_length(&self) -> f64 {
        self.total_steps as f64 / self.episodes as f64
    }

    pub fn average_reward(&self) -> f64 {
        self.total_reward / self.episodes as f64
    }

    pub fn steps_per_second(&self) -> f64 {
        self.total_steps as f64 / self.simulation_time.as_secs_f64()
    }
}

pub struct RandomAgent {
    rng: StdRng,
}

impl RandomAgent {
    pub fn with_seed(seed: u64) -> Self {
        Self {
            rng: StdRng::seed_from_u64(seed),
        }
    }

    pub fn run_episode(&mut self, environment: &mut GameState) -> Result<EpisodeStats, String> {
        let observation = environment.reset();
        validate_observation(&observation)?;

        let mut steps = 0;
        let mut total_reward = 0.0;
        loop {
            let legal_actions = environment.legal_actions();
            validate_actions(&legal_actions)?;
            if legal_actions.is_empty() {
                return Err("environment has no legal actions before termination".to_string());
            }

            let action = legal_actions[self.rng.gen_range(0..legal_actions.len())];
            if !legal_actions.contains(&action) {
                return Err("random agent selected an action outside legal_actions()".to_string());
            }

            let result = environment.step(action);
            steps += 1;
            total_reward += result.reward;
            validate_observation(&result.observation)?;

            if result.terminated || result.truncated {
                return Ok(EpisodeStats {
                    score: environment.score(),
                    total_reward,
                    steps,
                    terminated: result.terminated,
                    truncated: result.truncated,
                });
            }
        }
    }
}

pub fn evaluate_random_agent(
    episodes: usize,
    config: EnvironmentConfig,
    seed: u64,
) -> Result<EvaluationStats, String> {
    if episodes == 0 {
        return Err("random-agent evaluation requires at least one episode".to_string());
    }

    let started = Instant::now();
    let mut agent = RandomAgent::with_seed(seed);
    let mut environment = GameState::with_seed(config, seed);
    let mut evaluation = EvaluationStats {
        episodes,
        total_steps: 0,
        total_score: 0,
        highest_score: i32::MIN,
        lowest_score: i32::MAX,
        total_reward: 0.0,
        highest_total_reward: f32::NEG_INFINITY,
        lowest_total_reward: f32::INFINITY,
        longest_episode: 0,
        shortest_episode: usize::MAX,
        game_over_episodes: 0,
        truncated_episodes: 0,
        simulation_time: Duration::ZERO,
    };

    for _ in 0..episodes {
        let result = agent.run_episode(&mut environment)?;
        evaluation.total_steps += result.steps;
        evaluation.total_score += i64::from(result.score);
        evaluation.highest_score = evaluation.highest_score.max(result.score);
        evaluation.lowest_score = evaluation.lowest_score.min(result.score);
        evaluation.total_reward += f64::from(result.total_reward);
        evaluation.highest_total_reward = evaluation.highest_total_reward.max(result.total_reward);
        evaluation.lowest_total_reward = evaluation.lowest_total_reward.min(result.total_reward);
        evaluation.longest_episode = evaluation.longest_episode.max(result.steps);
        evaluation.shortest_episode = evaluation.shortest_episode.min(result.steps);
        evaluation.game_over_episodes += usize::from(result.terminated);
        evaluation.truncated_episodes += usize::from(result.truncated);
    }

    evaluation.simulation_time = started.elapsed();
    Ok(evaluation)
}

fn validate_observation(observation: &[[u8; GRID_WIDTH]; GRID_HEIGHT]) -> Result<(), String> {
    let piece_count = observation
        .iter()
        .flatten()
        .filter(|&&value| value != 0)
        .count();
    if piece_count > MAX_PIECES {
        return Err(format!("observation contains {piece_count} pieces"));
    }
    if observation.iter().flatten().any(|&value| value > 7) {
        return Err("observation contains an invalid piece value".to_string());
    }
    Ok(())
}

fn validate_actions(actions: &[Move]) -> Result<(), String> {
    if actions.iter().any(|action| {
        action.from == action.to
            || action.from.0 >= GRID_WIDTH
            || action.from.1 >= GRID_HEIGHT
            || action.to.0 >= GRID_WIDTH
            || action.to.1 >= GRID_HEIGHT
    }) {
        return Err("legal_actions() contains an invalid coordinate or no-op".to_string());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn random_agent_completes_one_episode() {
        let mut agent = RandomAgent::with_seed(7);
        let mut environment = GameState::with_seed(EnvironmentConfig::default(), 7);
        let result = agent.run_episode(&mut environment).unwrap();

        assert!(result.steps > 0);
        assert!(result.terminated || result.truncated);
        assert!(!(result.terminated && result.truncated));
    }

    #[test]
    fn random_agent_completes_many_episodes_with_truncation() {
        let stats = evaluate_random_agent(
            5,
            EnvironmentConfig {
                max_episode_steps: Some(5),
                ..EnvironmentConfig::default()
            },
            11,
        )
        .unwrap();

        assert_eq!(stats.episodes, 5);
        assert_eq!(stats.game_over_episodes + stats.truncated_episodes, 5);
        assert!(stats.total_steps >= 5);
        assert!(stats.lowest_score >= 0);
    }

    #[test]
    fn reset_starts_a_fresh_episode_after_game_over() {
        let mut environment = GameState::with_seed(
            EnvironmentConfig {
                max_episode_steps: Some(1),
                ..EnvironmentConfig::default()
            },
            13,
        );
        let action = environment.legal_actions()[0];
        let result = environment.step(action);
        assert!(result.truncated);

        let reset = environment.reset();
        assert_eq!(environment.score(), 0);
        assert!(!environment.game_over());
        assert_eq!(
            reset.iter().flatten().filter(|&&value| value != 0).count(),
            5
        );
    }

    #[test]
    fn evaluation_rejects_zero_episodes() {
        assert!(evaluate_random_agent(0, EnvironmentConfig::default(), 0).is_err());
    }
}
