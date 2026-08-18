use crate::constants::{Coord, GRID_HEIGHT, GRID_WIDTH};
use crate::types::PieceColor;
use petgraph::algo::astar;
use petgraph::Graph;
use std::collections::{HashMap, HashSet};

pub fn has_legal_move(occupied: &HashSet<Coord>) -> bool {
    // A completely full board has no legal destination.
    if occupied.len() == GRID_WIDTH * GRID_HEIGHT {
        return false;
    }

    // Try every occupied cell as a source.
    for &start in occupied {
        // Try every empty tile as a destination.
        for y in 0..GRID_HEIGHT {
            for x in 0..GRID_WIDTH {
                let destination = (x, y);

                if occupied.contains(&destination) {
                    continue;
                }

                if find_path(start, destination, occupied).is_some() {
                    return true;
                }
            }
        }
    }

    false
}

/// Finds an A* path from start to destination.
///
/// Returns Some(path) when the destination is reachable,
/// otherwise None.
pub fn find_path(
    start: Coord,
    destination: Coord,
    occupied: &HashSet<Coord>,
) -> Option<Vec<Coord>> {
    if start == destination
        || start.0 >= GRID_WIDTH
        || start.1 >= GRID_HEIGHT
        || destination.0 >= GRID_WIDTH
        || destination.1 >= GRID_HEIGHT
        || occupied.contains(&destination)
    {
        return None;
    }

    let mut graph = Graph::<Coord, ()>::new();

    let mut node_indices = vec![vec![None; GRID_WIDTH]; GRID_HEIGHT];

    // Create nodes for every non-blocked cell.
    for y in 0..GRID_HEIGHT {
        for x in 0..GRID_WIDTH {
            let coord = (x, y);

            if !occupied.contains(&coord) || coord == start {
                let node = graph.add_node(coord);
                node_indices[y][x] = Some(node);
            }
        }
    }

    // Connect horizontally and vertically adjacent cells.
    for y in 0..GRID_HEIGHT {
        for x in 0..GRID_WIDTH {
            if let Some(node) = node_indices[y][x] {
                let neighbors = [
                    (x.wrapping_sub(1), y),
                    (x + 1, y),
                    (x, y.wrapping_sub(1)),
                    (x, y + 1),
                ];

                for (nx, ny) in neighbors {
                    if nx >= GRID_WIDTH || ny >= GRID_HEIGHT {
                        continue;
                    }

                    if let Some(neighbor_node) = node_indices[ny][nx] {
                        graph.add_edge(node, neighbor_node, ());
                    }
                }
            }
        }
    }

    let start_node = node_indices[start.1][start.0]?;
    let destination_node = node_indices[destination.1][destination.0]?;

    let result = astar(
        &graph,
        start_node,
        |node| node == destination_node,
        |_| 1,
        |_| 0,
    );

    result.map(|(_, path)| {
        path.into_iter()
            .filter_map(|node| graph.node_weight(node).copied())
            .collect()
    })
}

pub fn score_and_find_matched_pieces(
    piece_map: &HashMap<Coord, PieceColor>,
    grid_size: usize,
) -> (i32, HashSet<Coord>) {
    let directions = [(1isize, 0isize), (0, 1), (1, 1), (1, -1)];
    let mut score = 0;
    let mut matched_pieces = HashSet::new();

    for y in 0..grid_size {
        for x in 0..grid_size {
            let coord = (x, y);
            let Some(color) = piece_map.get(&coord) else {
                continue;
            };

            for (dir_x, dir_y) in directions {
                let previous_x = x as isize - dir_x;
                let previous_y = y as isize - dir_y;
                if is_in_grid(previous_x, previous_y, grid_size)
                    && piece_map.get(&(previous_x as usize, previous_y as usize)) == Some(color)
                {
                    continue;
                }

                let mut line = Vec::new();
                let mut current_x = x as isize;
                let mut current_y = y as isize;
                while is_in_grid(current_x, current_y, grid_size)
                    && piece_map.get(&(current_x as usize, current_y as usize)) == Some(color)
                {
                    line.push((current_x as usize, current_y as usize));
                    current_x += dir_x;
                    current_y += dir_y;
                }

                if line.len() >= 5 {
                    score += calculate_score(line.len());
                    matched_pieces.extend(line);
                }
            }
        }
    }

    (score, matched_pieces)
}

fn is_in_grid(x: isize, y: isize, grid_size: usize) -> bool {
    x >= 0 && x < grid_size as isize && y >= 0 && y < grid_size as isize
}

fn calculate_score(length: usize) -> i32 {
    match length {
        5 => 10,
        6 => 12,
        7 => 14,
        8 => 16,
        9 => 18,
        _ => 0,
    }
}
