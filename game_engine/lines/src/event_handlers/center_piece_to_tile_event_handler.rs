use bevy::math::Vec3;
use bevy::prelude::{EventReader, Query, Res, Transform, With, Without};

use crate::components::{Piece, Tile};
use crate::events::CenterPieceToTileEvent;
use crate::resources::SelectionInfo;

pub fn center_piece_to_tile_event_handler(
    mut center_piece_to_tile_events: EventReader<CenterPieceToTileEvent>,
    q_tiles: Query<&Transform, (With<Tile>, Without<Piece>)>,
    mut q_pieces: Query<(&mut Transform, &mut Piece), (With<Piece>, Without<Tile>)>,
    selection_info: Res<SelectionInfo>,
) {
    if !selection_info.is_choosing() {
        return;
    }

    for center_piece_to_tile_event in center_piece_to_tile_events.read() {
        let piece_id = center_piece_to_tile_event.piece_id();
        let tile_id = center_piece_to_tile_event.tile_id();

        if let Ok(tile_transform) = q_tiles.get(tile_id) {
            if let Ok(piece_info) = q_pieces.get_mut(piece_id) {
                let (mut piece_transform, mut piece) = piece_info;

                let x = tile_transform.translation.x;
                let y = tile_transform.translation.y;
                let z = piece_transform.translation.z;

                piece_transform.translation = Vec3::new(x, y, z);
                piece.bouncer().reset();
            }
        }
    }
}
