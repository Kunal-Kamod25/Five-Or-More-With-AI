use bevy::prelude::Color;
use rand::Rng;

#[derive(Clone, PartialEq)]
pub enum PieceColor {
    Red,
    Green,
    Blue,
    Yellow,
    Purple,
    Cyan,
    Orange,
}

impl PieceColor {
    pub fn observation_value(&self) -> u8 {
        use PieceColor::*;
        match self {
            Red => 1,
            Green => 2,
            Blue => 3,
            Yellow => 4,
            Purple => 5,
            Cyan => 6,
            Orange => 7,
        }
    }

    pub fn choose_piece_color() -> Self {
        let mut rng = rand::thread_rng();
        Self::choose_piece_color_with_rng(&mut rng)
    }

    pub fn choose_piece_color_with_rng<R: Rng + ?Sized>(rng: &mut R) -> Self {
        use PieceColor::*;
        match rng.gen_range(0..7) {
            0 => Red,
            1 => Green,
            2 => Blue,
            3 => Yellow,
            4 => Purple,
            5 => Cyan,
            _ => Orange,
        }
    }

    pub fn get_color(&self) -> Color {
        use PieceColor::*;
        match self {
            Red => Color::rgb(1.0, 0.0, 0.0),
            Green => Color::rgb(0.0, 1.0, 0.0),
            Blue => Color::rgb(0.0, 0.0, 1.0),
            Yellow => Color::rgb(1.0, 1.0, 0.0),
            Purple => Color::rgb(1.0, 0.0, 1.0),
            Cyan => Color::rgb(0.0, 1.0, 1.0),
            Orange => Color::rgb(1.0, 0.5, 0.0),
        }
    }
}
