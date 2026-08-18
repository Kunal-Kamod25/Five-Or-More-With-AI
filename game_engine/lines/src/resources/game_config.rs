use bevy::prelude::Resource;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Difficulty {
    Easy,
    Medium,
    Hard,
}

impl Difficulty {
    pub fn spawn_amount(self) -> usize {
        match self {
            Self::Easy => 1,
            Self::Medium => 2,
            Self::Hard => 3,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Self::Easy => "Easy",
            Self::Medium => "Medium",
            Self::Hard => "Hard",
        }
    }
}

#[derive(Resource, Debug, Default)]
pub struct GameConfig {
    difficulty: Option<Difficulty>,
}

impl GameConfig {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn difficulty(&self) -> Option<Difficulty> {
        self.difficulty
    }

    pub fn set_difficulty(&mut self, difficulty: Difficulty) {
        self.difficulty = Some(difficulty);
    }

    pub fn clear_difficulty(&mut self) {
        self.difficulty = None;
    }

    pub fn spawn_amount(&self) -> Option<usize> {
        self.difficulty.map(Difficulty::spawn_amount)
    }
}

#[cfg(test)]
mod tests {
    use super::Difficulty;

    #[test]
    fn easy_spawns_one_piece() {
        assert_eq!(Difficulty::Easy.spawn_amount(), 1);
    }

    #[test]
    fn medium_spawns_two_pieces() {
        assert_eq!(Difficulty::Medium.spawn_amount(), 2);
    }

    #[test]
    fn hard_spawns_three_pieces() {
        assert_eq!(Difficulty::Hard.spawn_amount(), 3);
    }
}
