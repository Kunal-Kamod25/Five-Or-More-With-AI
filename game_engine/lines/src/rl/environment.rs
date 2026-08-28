use rand::rngs::StdRng;
use rand::SeedableRng;
use std::collections::{HashMap, HashSet};

use crate::constants::{Coord, GRID_HEIGHT, GRID_WIDTH, MAX_PIECES};
use crate::game_logic::{
    board_to_matrix, create_seed_pieces, find_path, has_legal_move, score_and_find_matched_pieces,
};
use crate::types::PieceColor;

pub type Observation = [[u8; GRID_WIDTH]; GRID_HEIGHT];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Move {
    pub from: Coord,
    pub to: Coord,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct EnvironmentConfig {
    pub spawn_amount: usize,
    pub initial_piece_count: usize,
    pub max_episode_steps: Option<usize>,
}

impl Default for EnvironmentConfig {
    fn default() -> Self {
        Self {
            spawn_amount: 2,
            initial_piece_count: 5,
            max_episode_steps: None,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct StepResult {
    pub observation: Observation,
    pub reward: f32,
    pub terminated: bool,
    pub truncated: bool,
}

pub struct GameState {
    board: HashMap<Coord, PieceColor>,
    score: i32,
    episode_steps: usize,
    terminated: bool,
    truncated: bool,
    config: EnvironmentConfig,
    rng: StdRng,
}

impl GameState {
    pub fn new() -> Self {
        Self::with_config(EnvironmentConfig::default())
    }

    pub fn with_config(config: EnvironmentConfig) -> Self {
        Self::with_seed(config, 0)
    }

    pub fn with_seed(config: EnvironmentConfig, seed: u64) -> Self {
        let mut environment = Self {
            board: HashMap::new(),
            score: 0,
            episode_steps: 0,
            terminated: false,
            truncated: false,
            config,
            rng: StdRng::seed_from_u64(seed),
        };
        environment.reset();
        environment
    }

    pub fn reset(&mut self) -> Observation {
        self.board.clear();
        self.score = 0;
        self.episode_steps = 0;
        self.terminated = false;
        self.truncated = false;
        self.spawn(self.config.initial_piece_count);
        self.observation()
    }

    pub fn observation(&self) -> Observation {
        board_to_matrix(&self.board)
    }

    pub fn score(&self) -> i32 {
        self.score
    }

    pub fn game_over(&self) -> bool {
        self.terminated
    }

    pub fn legal_actions(&self) -> Vec<Move> {
        let occupied = self.occupied();
        let mut actions = Vec::new();
        for &from in self.board.keys() {
            for y in 0..GRID_HEIGHT {
                for x in 0..GRID_WIDTH {
                    let to = (x, y);
                    if !occupied.contains(&to) && find_path(from, to, &occupied).is_some() {
                        actions.push(Move { from, to });
                    }
                }
            }
        }
        actions
    }

    pub fn step(&mut self, action: Move) -> StepResult {
        if self.terminated || self.truncated {
            return self.result(-1.0);
        }

        let occupied = self.occupied();
        let Some(color) = self.board.get(&action.from).cloned() else {
            return self.result(-1.0);
        };
        if self.board.contains_key(&action.to)
            || find_path(action.from, action.to, &occupied).is_none()
        {
            return self.result(-1.0);
        }

        self.board.remove(&action.from);
        self.board.insert(action.to, color);
        self.episode_steps += 1;

        let (cleared_score, matched) =
            score_and_find_matched_pieces(&self.board, GRID_WIDTH.min(GRID_HEIGHT));
        let mut reward = 0.0;
        if !matched.is_empty() {
            reward = cleared_score as f32;
            self.score += cleared_score;
            for coord in matched {
                self.board.remove(&coord);
            }
        } else {
            self.spawn(self.config.spawn_amount);
        }

        if self.board.len() == MAX_PIECES || !has_legal_move(&self.occupied()) {
            self.terminated = true;
            reward -= 1.0;
        }
        if self
            .config
            .max_episode_steps
            .is_some_and(|limit| self.episode_steps >= limit)
            && !self.terminated
        {
            self.truncated = true;
        }

        self.result(reward)
    }

    fn spawn(&mut self, amount: usize) {
        let pieces = create_seed_pieces(amount, &self.occupied(), &mut self.rng);
        self.board.extend(pieces);
    }

    fn occupied(&self) -> HashSet<Coord> {
        self.board.keys().copied().collect()
    }

    fn result(&self, reward: f32) -> StepResult {
        StepResult {
            observation: self.observation(),
            reward,
            terminated: self.terminated,
            truncated: self.truncated,
        }
    }
}

impl Default for GameState {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn empty_config() -> EnvironmentConfig {
        EnvironmentConfig {
            spawn_amount: 0,
            initial_piece_count: 0,
            max_episode_steps: None,
        }
    }

    fn board_with(entries: &[(Coord, PieceColor)]) -> GameState {
        let mut environment = GameState::with_seed(empty_config(), 1);
        environment.board.extend(entries.iter().cloned());
        environment
    }

    #[test]
    fn reset_produces_valid_observation_and_five_pieces() {
        let environment = GameState::with_seed(EnvironmentConfig::default(), 1);
        let observation = environment.observation();

        assert_eq!(observation.len(), 9);
        assert!(observation.iter().all(|row| row.len() == 9));
        assert_eq!(
            observation
                .iter()
                .flatten()
                .filter(|&&value| value != 0)
                .count(),
            5
        );
        assert!(observation.iter().flatten().all(|&value| value <= 7));
    }

    #[test]
    fn legal_move_changes_only_source_and_destination() {
        let mut environment = board_with(&[((0, 0), PieceColor::Red)]);
        let result = environment.step(Move {
            from: (0, 0),
            to: (1, 0),
        });

        assert_eq!(result.reward, 0.0);
        assert_eq!(result.observation[0][0], 0);
        assert_eq!(result.observation[0][1], 1);
    }

    #[test]
    fn invalid_move_leaves_board_unchanged() {
        let mut environment = board_with(&[((0, 0), PieceColor::Red), ((1, 0), PieceColor::Blue)]);
        let before = environment.observation();
        let result = environment.step(Move {
            from: (0, 0),
            to: (1, 0),
        });

        assert_eq!(result.reward, -1.0);
        assert_eq!(result.observation, before);
    }

    #[test]
    fn clearing_line_gives_positive_score_reward() {
        let mut entries = (0..4)
            .map(|x| ((x, 0), PieceColor::Red))
            .collect::<Vec<_>>();
        entries.push(((0, 1), PieceColor::Red));
        let mut environment = board_with(&entries);

        let result = environment.step(Move {
            from: (0, 1),
            to: (4, 0),
        });

        assert!(result.reward > 0.0);
        assert_eq!(environment.score(), 10);
        assert_eq!(result.observation, [[0; 9]; 9]);
    }

    #[test]
    fn legal_actions_are_reachable_empty_destinations() {
        let environment = board_with(&[((0, 0), PieceColor::Red), ((1, 0), PieceColor::Blue)]);

        assert!(!environment.legal_actions().contains(&Move {
            from: (0, 0),
            to: (1, 0),
        }));
        assert!(environment.legal_actions().iter().all(|action| {
            action.from != action.to
                && action.from.0 < 9
                && action.from.1 < 9
                && action.to.0 < 9
                && action.to.1 < 9
        }));
    }

    #[test]
    fn filling_the_last_empty_cell_terminates_the_episode() {
        let entries = (0..9)
            .flat_map(|y| {
                (0..9).map(move |x| {
                    (
                        (x, y),
                        match (x + 2 * y) % 7 {
                            0 => PieceColor::Red,
                            1 => PieceColor::Green,
                            2 => PieceColor::Blue,
                            3 => PieceColor::Yellow,
                            4 => PieceColor::Purple,
                            5 => PieceColor::Cyan,
                            _ => PieceColor::Orange,
                        },
                    )
                })
            })
            .filter(|(coord, _)| *coord != (1, 0))
            .collect::<Vec<_>>();
        let mut environment = GameState::with_config(EnvironmentConfig {
            spawn_amount: 2,
            initial_piece_count: 0,
            max_episode_steps: None,
        });
        environment.board.extend(entries);

        let result = environment.step(Move {
            from: (0, 0),
            to: (1, 0),
        });

        assert!(result.terminated);
        assert!(!result.truncated);
        let reset_observation = environment.reset();
        assert!(!environment.game_over());
        assert_eq!(
            reset_observation
                .iter()
                .flatten()
                .filter(|&&value| value != 0)
                .count(),
            0
        );
    }

    #[test]
    fn episode_limit_truncates_and_reset_is_fresh() {
        let mut environment = GameState::with_seed(
            EnvironmentConfig {
                max_episode_steps: Some(1),
                initial_piece_count: 1,
                ..empty_config()
            },
            1,
        );
        environment.board.insert((0, 0), PieceColor::Red);
        let result = environment.step(Move {
            from: (0, 0),
            to: (1, 0),
        });

        assert!(result.truncated);
        assert!(!result.terminated);
        assert!(environment
            .reset()
            .iter()
            .flatten()
            .any(|&value| value != 0));
        assert!(!environment.game_over());
    }
}
