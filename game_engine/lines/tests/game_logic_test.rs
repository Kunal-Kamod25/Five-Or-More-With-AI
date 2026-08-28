use std::collections::HashMap;
use std::collections::HashSet;

use lines::game_logic::{board_to_matrix, find_path, score_and_find_matched_pieces};
use lines::types::PieceColor;

#[test]
fn test_empty_board_produces_a_9_by_9_zero_matrix() {
    let matrix = board_to_matrix(&HashMap::new());

    assert_eq!(matrix, [[0; 9]; 9]);
    assert_eq!(matrix.len(), 9);
    assert!(matrix.iter().all(|row| row.len() == 9));
}

#[test]
fn test_piece_is_written_at_matrix_y_then_x_position() {
    let piece_map = HashMap::from([((4, 2), PieceColor::Blue)]);

    let matrix = board_to_matrix(&piece_map);

    assert_eq!(matrix[2][4], 3);
    assert_eq!(
        matrix.iter().flatten().filter(|&&value| value != 0).count(),
        1
    );
}

#[test]
fn test_piece_colors_have_distinct_stable_values() {
    let colors = [
        PieceColor::Red,
        PieceColor::Green,
        PieceColor::Blue,
        PieceColor::Yellow,
        PieceColor::Purple,
        PieceColor::Cyan,
        PieceColor::Orange,
    ];
    let values = colors
        .iter()
        .map(PieceColor::observation_value)
        .collect::<Vec<_>>();
    let repeated_color_map = HashMap::from([((1, 1), PieceColor::Red), ((7, 7), PieceColor::Red)]);
    let repeated_color_matrix = board_to_matrix(&repeated_color_map);

    assert_eq!(values, vec![1, 2, 3, 4, 5, 6, 7]);
    assert_eq!(repeated_color_matrix[1][1], 1);
    assert_eq!(repeated_color_matrix[7][7], 1);
}

#[test]
fn test_multiple_pieces_are_represented_and_empty_cells_remain_zero() {
    let piece_map = HashMap::from([
        ((0, 0), PieceColor::Red),
        ((8, 8), PieceColor::Orange),
        ((3, 6), PieceColor::Cyan),
    ]);

    let matrix = board_to_matrix(&piece_map);

    assert_eq!(matrix[0][0], 1);
    assert_eq!(matrix[8][8], 7);
    assert_eq!(matrix[6][3], 6);
    assert_eq!(matrix[4][4], 0);
}

#[test]
fn test_path_exists_when_destination_is_reachable() {
    let occupied = HashSet::new();

    let start = (0, 0);
    let destination = (2, 2);

    let path = find_path(start, destination, &occupied);

    assert!(path.is_some());

    let path = path.unwrap();

    assert_eq!(path.first(), Some(&start));
    assert_eq!(path.last(), Some(&destination));
}
#[test]
fn test_path_does_not_exist_when_destination_is_blocked() {
    let mut occupied = HashSet::new();

    // Block the cells around the starting position.
    occupied.insert((1, 0));
    occupied.insert((0, 1));

    let start = (0, 0);
    let destination = (2, 2);

    let path = find_path(start, destination, &occupied);

    assert!(path.is_none());
}
#[test]
fn test_legal_move_exists_on_partially_filled_board() {
    let mut occupied = HashSet::new();

    // One piece at (0, 0), with the rest of the board empty.
    occupied.insert((0, 0));

    assert!(lines::game_logic::has_legal_move(&occupied));
}
#[test]
fn test_no_legal_move_when_board_is_full() {
    let mut occupied = HashSet::new();

    for y in 0..9 {
        for x in 0..9 {
            occupied.insert((x, y));
        }
    }

    assert!(!lines::game_logic::has_legal_move(&occupied));
}

#[test]
fn test_path_does_not_exist_when_destination_is_occupied() {
    let occupied = HashSet::from([(0, 0), (2, 2)]);

    assert!(find_path((0, 0), (2, 2), &occupied).is_none());
}

#[test]
fn test_path_does_not_exist_for_invalid_coordinates() {
    let occupied = HashSet::from([(0, 0)]);

    assert!(find_path((9, 0), (2, 2), &occupied).is_none());
    assert!(find_path((0, 0), (9, 2), &occupied).is_none());
}

#[test]
fn test_path_does_not_exist_when_start_equals_destination() {
    let occupied = HashSet::from([(2, 2)]);

    assert!(find_path((2, 2), (2, 2), &occupied).is_none());
}

#[test]
fn test_horizontal_lines_score_and_remove_exact_lengths() {
    for length in 5..=9 {
        let piece_map = (0..length)
            .map(|x| ((x, 0), PieceColor::Red))
            .collect::<HashMap<_, _>>();

        let (score, matched_pieces) = score_and_find_matched_pieces(&piece_map, 9);

        assert_eq!(score, length as i32 * 2);
        assert_eq!(matched_pieces.len(), length);
    }
}

#[test]
fn test_vertical_and_diagonal_lines_are_detected() {
    let vertical = (0..5)
        .map(|index| ((8, index), PieceColor::Blue))
        .collect::<HashMap<_, _>>();
    let diagonal_down = (0..5)
        .map(|index| ((index, index), PieceColor::Green))
        .collect::<HashMap<_, _>>();
    let diagonal_up = (0..5)
        .map(|index| ((index, 8 - index), PieceColor::Yellow))
        .collect::<HashMap<_, _>>();

    for piece_map in [vertical, diagonal_down, diagonal_up] {
        let (score, matched_pieces) = score_and_find_matched_pieces(&piece_map, 9);

        assert_eq!(score, 10);
        assert_eq!(matched_pieces.len(), 5);
    }
}

#[test]
fn test_intersecting_lines_are_scored_and_removed_once() {
    let mut piece_map = HashMap::new();
    for index in 0..5 {
        piece_map.insert((index, 2), PieceColor::Purple);
        piece_map.insert((2, index), PieceColor::Purple);
    }

    let (score, matched_pieces) = score_and_find_matched_pieces(&piece_map, 9);

    assert_eq!(score, 20);
    assert_eq!(matched_pieces.len(), 9);
}

#[test]
fn test_short_runs_are_not_matched() {
    let piece_map = (0..4)
        .map(|x| ((x, 0), PieceColor::Cyan))
        .collect::<HashMap<_, _>>();

    let (score, matched_pieces) = score_and_find_matched_pieces(&piece_map, 9);

    assert_eq!(score, 0);
    assert!(matched_pieces.is_empty());
}
