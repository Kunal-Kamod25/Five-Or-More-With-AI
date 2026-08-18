use std::collections::HashSet;

use bevy::math::Vec2;
use bevy::prelude::{EventReader, Query, ResMut, Transform, With};

use crate::components::{Piece, Tile};
use crate::constants::Coord;
use crate::events::CalculateMovementPathEvent;
use crate::game_logic::find_path;
use crate::resources::SelectionInfo;

pub fn calculate_movement_path_event_handler(
    q_pieces: Query<&Piece, With<Piece>>,
    q_tiles: Query<(&Transform, &Tile), With<Tile>>,
    mut selection_info: ResMut<SelectionInfo>,
    mut calculate_movement_path_events: EventReader<CalculateMovementPathEvent>,
) {
    if !selection_info.is_choosing() {
        return;
    }

    for event in calculate_movement_path_events.read() {
        let piece_id = event.piece_id();
        let tile_id = event.target_tile_id();

        let Ok(selected_piece) = q_pieces.get(piece_id) else {
            continue;
        };
        let Ok((_, tile)) = q_tiles.get(tile_id) else {
            continue;
        };

        let from = selected_piece.coord();
        let to = tile.coord();

        let occupied = q_pieces.iter().map(Piece::coord).collect::<HashSet<_>>();
        let Some(path) = find_path(from, to, &occupied) else {
            continue;
        };

        let world_path = convert_path_from_coord_to_world(path, &q_tiles);

        selection_info.set_dest_coord(to); // deferring setting the coord until the end
        selection_info.set_path(world_path);
        selection_info.start_moving();
    }
}

fn convert_path_from_coord_to_world(
    path: Vec<Coord>,
    q_tiles: &Query<(&Transform, &Tile), With<Tile>>,
) -> Vec<Vec2> {
    path.iter()
        .filter_map(|coord| {
            q_tiles
                .iter()
                .find(|(_, tile)| tile.coord() == *coord)
                .map(|(transform, _)| transform.translation.truncate())
        })
        .collect()
}
