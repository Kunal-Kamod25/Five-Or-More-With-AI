// Kunal's part: Writing the bridge between Khumba's Rust game and my Python AI.
// Using PyO3 to expose the game logic so I don't have to rewrite everything in Python!
use pyo3::prelude::*;
use std::collections::{HashSet, HashMap};
use crate::game_logic::{has_legal_move, find_path, score_and_find_matched_pieces};
use crate::types::PieceColor;

#[pyfunction]
fn py_has_legal_move(occupied_list: Vec<(usize, usize)>) -> bool {
    let occupied: HashSet<(usize, usize)> = occupied_list.into_iter().collect();
    has_legal_move(&occupied)
}

#[pyfunction]
fn py_find_path(start: (usize, usize), destination: (usize, usize), occupied_list: Vec<(usize, usize)>) -> Option<Vec<(usize, usize)>> {
    let occupied: HashSet<(usize, usize)> = occupied_list.into_iter().collect();
    find_path(start, destination, &occupied)
}

#[pyfunction]
fn py_score_and_find_matched_pieces(piece_dict: HashMap<(usize, usize), u8>, grid_size: usize) -> (i32, Vec<(usize, usize)>) {
    let mut piece_map = HashMap::new();
    for (coord, color_idx) in piece_dict {
        let color = match color_idx {
            0 => PieceColor::Red,
            1 => PieceColor::Green,
            2 => PieceColor::Blue,
            3 => PieceColor::Yellow,
            4 => PieceColor::Purple,
            5 => PieceColor::Cyan,
            _ => PieceColor::Orange,
        };
        piece_map.insert(coord, color);
    }
    let (score, matched) = score_and_find_matched_pieces(&piece_map, grid_size);
    (score, matched.into_iter().collect())
}

#[pymodule]
fn lines_logic(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_has_legal_move, m)?)?;
    m.add_function(wrap_pyfunction!(py_find_path, m)?)?;
    m.add_function(wrap_pyfunction!(py_score_and_find_matched_pieces, m)?)?;
    Ok(())
}
