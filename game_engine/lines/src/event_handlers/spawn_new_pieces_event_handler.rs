use std::collections::HashSet;

use bevy::asset::AssetServer;
use bevy::math::Vec3;
use bevy::prelude::{
    default, Commands, EventReader, EventWriter, Query, Res, Sprite, SpriteBundle, Transform,
};
use rand::seq::SliceRandom;

use crate::actions::tile_to_world_pos;
use crate::components::Piece;
use crate::constants::{Coord, BALL_LAYER, BALL_SCALE, GRID_HEIGHT, GRID_WIDTH, MAX_PIECES};
use crate::events::{NextPlannedMove, ShowGameOverEvent, SpawnNewPiecesEvent, ValidateMoveEvent};
use crate::resources::SelectionInfo;
use crate::types::PieceColor;

pub fn spawn_new_pieces_event_handler(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    q_pieces: Query<&Piece>,
    mut validate_move_event_writer: EventWriter<ValidateMoveEvent>,
    mut spawn_new_pieces_event_reader: EventReader<SpawnNewPiecesEvent>,
    mut show_game_over_event_writer: EventWriter<ShowGameOverEvent>,
    selection_info: Res<SelectionInfo>,
) {
    if selection_info.is_game_over() {
        return;
    }

    for spawn_new_pieces_event in spawn_new_pieces_event_reader.read() {
        let taken_pieces = q_pieces
            .iter()
            .map(|piece| piece.coord())
            .collect::<HashSet<Coord>>();
        let amount = spawn_new_pieces_event.amount();
        let diff = MAX_PIECES.saturating_sub(taken_pieces.len());
        let amount = amount.min(diff);

        if amount == 0 {
            show_game_over_event_writer.send(ShowGameOverEvent);
            return;
        }

        let pieces_to_create = create_seed_pieces(amount, &taken_pieces);

        for (coord, piece_color) in pieces_to_create.into_iter() {
            commands.spawn((
                SpriteBundle {
                    texture: asset_server.load("sprites/ball.png"),
                    transform: Transform::default()
                        .with_translation(tile_to_world_pos(coord).extend(BALL_LAYER))
                        .with_scale(Vec3::splat(BALL_SCALE)),
                    sprite: Sprite {
                        color: piece_color.get_color(),
                        ..default()
                    },
                    ..default()
                },
                Piece::new(coord, piece_color.clone()),
            ));
        }

        validate_move_event_writer.send(ValidateMoveEvent::new(NextPlannedMove::Play));
    }
}

fn create_seed_pieces(amount: usize, taken_pieces: &HashSet<Coord>) -> Vec<(Coord, PieceColor)> {
    let mut rng = rand::thread_rng();
    let mut available_positions = (0..GRID_HEIGHT)
        .flat_map(|y| (0..GRID_WIDTH).map(move |x| (x, y)))
        .filter(|coord| !taken_pieces.contains(coord))
        .collect::<Vec<_>>();
    available_positions.shuffle(&mut rng);

    available_positions
        .into_iter()
        .take(amount)
        .map(|coord| (coord, PieceColor::choose_piece_color()))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::create_seed_pieces;
    use crate::constants::{GRID_HEIGHT, GRID_WIDTH};
    use std::collections::HashSet;

    #[test]
    fn spawning_zero_pieces_is_safe() {
        let taken = HashSet::new();

        assert!(create_seed_pieces(0, &taken).is_empty());
    }

    #[test]
    fn spawning_near_full_board_uses_only_empty_cells() {
        let mut taken = (0..GRID_HEIGHT)
            .flat_map(|y| (0..GRID_WIDTH).map(move |x| (x, y)))
            .collect::<HashSet<_>>();
        taken.remove(&(4, 4));

        let pieces = create_seed_pieces(3, &taken);

        assert_eq!(pieces.len(), 1);
        assert_eq!(pieces[0].0, (4, 4));
    }
}
