use bevy::prelude::Resource;

#[derive(Resource, Debug, Default)]
pub struct HighScore(pub i32);

impl HighScore {
    pub fn new() -> Self {
        Self(0)
    }

    pub fn update(&mut self, score: i32) {
        self.0 = self.0.max(score);
    }
}

#[cfg(test)]
mod tests {
    use super::HighScore;

    #[test]
    fn high_score_only_increases() {
        let mut high_score = HighScore::new();

        high_score.update(20);
        high_score.update(10);

        assert_eq!(high_score.0, 20);
    }
}
