use crate::components::Piece;
use crate::constants::{GRID_HEIGHT, GRID_WIDTH};
use crate::types::PieceColor;
use bevy::prelude::*;
use std::fs;
use std::io::Write;

pub fn log_board_matrix_system(
    query: Query<&Piece>,
    mut last_state: Local<String>,
) {
    let mut board = vec![vec![0; GRID_WIDTH]; GRID_HEIGHT];
    
    // Map colors to integers (1 to 7)
    for piece in query.iter() {
        let (x, y) = piece.coord();
        if x >= GRID_WIDTH || y >= GRID_HEIGHT {
            continue;
        }
        
        let color_val = match piece.piece_color() {
            PieceColor::Red => 1,
            PieceColor::Green => 2,
            PieceColor::Blue => 3,
            PieceColor::Yellow => 4,
            PieceColor::Purple => 5,
            PieceColor::Cyan => 6,
            PieceColor::Orange => 7,
        };
        board[y][x] = color_val;
    }
    
    // Format the matrix into a string
    let mut matrix_str = String::new();
    for y in (0..GRID_HEIGHT).rev() {
        for x in 0..GRID_WIDTH {
            matrix_str.push_str(&format!("{} ", board[y][x]));
        }
        matrix_str.push('\n');
    }
    
    // Only write to file if the state has changed
    if *last_state != matrix_str {
        *last_state = matrix_str.clone();
        
        // Write to data/raw directory relative to the workspace root
        // When running via `cargo run` from game_engine/lines, the path is ../../data/raw/
        if let Ok(mut file) = fs::File::create("../../data/raw/board_matrix_live.txt") {
            let _ = file.write_all(matrix_str.as_bytes());
        }
    }
}
