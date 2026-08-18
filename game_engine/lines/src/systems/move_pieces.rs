use crate::components::Piece;
use crate::constants::BALL_SPEED;
use crate::events::{NextPlannedMove, ValidateMoveEvent};
use crate::resources::SelectionInfo;
use bevy::prelude::{EventWriter, Query, Res, ResMut, Time, Transform, With};

pub fn move_pieces(
    time: Res<Time>,
    mut q_pieces: Query<(&mut Transform, &mut Piece), With<Piece>>,
    mut selection_info: ResMut<SelectionInfo>,
    mut validate_move_event_writer: EventWriter<ValidateMoveEvent>,
) {
    if !selection_info.is_moving() {
        return;
    }

    if let Some(selected_piece) = selection_info.selected() {
        if let Some((mut transform, mut piece)) = q_pieces.get_mut(selected_piece).ok() {
            if let Some(&next_destination) = selection_info.get_path().first() {
                let dt = time.delta_seconds();
                let target = next_destination.extend(transform.translation.z);
                let distance = transform.translation.distance(target);
                let step = BALL_SPEED * dt;

                if distance <= step || distance < 0.1 {
                    transform.translation = target;
                    selection_info.pop_path();
                    if selection_info.empty_path() {
                        if let Some(coord) = selection_info.pop_dest_coord() {
                            piece.set_coord(coord);
                        } else {
                            selection_info.start_choosing();
                        }

                        selection_info.deselect();
                        selection_info.validate_move();
                        validate_move_event_writer
                            .send(ValidateMoveEvent::new(NextPlannedMove::SpawnPieces));
                    }
                } else if distance > 0.0 {
                    let direction = (target - transform.translation) / distance;
                    transform.translation += direction * step;
                }
            }
        }
    }
}
