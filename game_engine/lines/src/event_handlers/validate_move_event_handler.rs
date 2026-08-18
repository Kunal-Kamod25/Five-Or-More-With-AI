use std::collections::{HashMap, HashSet};

use bevy::prelude::{
    Commands, Entity, EventReader, EventWriter, ParamSet, Query, Res, ResMut, Text, With,
};

use crate::components::{HighScoreText, Piece, ScoreText};
use crate::constants::{Coord, GRID_HEIGHT, GRID_WIDTH};
use crate::events::{NextPlannedMove, ShowGameOverEvent, SpawnNewPiecesEvent, ValidateMoveEvent};
use crate::game_logic::{has_legal_move, score_and_find_matched_pieces};
use crate::resources::{GameConfig, HighScore, Score, SelectionInfo};

pub fn validate_move_event_handler(
    mut validate_move_event_reader: EventReader<ValidateMoveEvent>,
    mut spawn_new_pieces_event_writer: EventWriter<SpawnNewPiecesEvent>,
    mut commands: Commands,
    mut score: ResMut<Score>,
    mut score_texts: ParamSet<(
        Query<&mut Text, With<ScoreText>>,
        Query<&mut Text, With<HighScoreText>>,
    )>,
    q_pieces: Query<(Entity, &Piece), With<Piece>>,
    mut selection_info: ResMut<SelectionInfo>,
    mut show_game_over_event_writer: EventWriter<ShowGameOverEvent>,
    game_config: Res<GameConfig>,
    mut high_score: ResMut<HighScore>,
) {
    if selection_info.is_game_over() {
        return;
    }

    for validate_move_event in validate_move_event_reader.read() {
        let mut next_planned_move = validate_move_event.next_planned_move();

        let piece_map = q_pieces
            .iter()
            .map(|(_, piece)| (piece.coord(), piece.piece_color()))
            .collect::<HashMap<Coord, _>>();

        let (total_score, matched_pieces) =
            score_and_find_matched_pieces(&piece_map, GRID_WIDTH.min(GRID_HEIGHT));
        if !matched_pieces.is_empty() {
            next_planned_move = NextPlannedMove::Play;

            score.add(total_score);
            let previous_high_score = high_score.0;
            high_score.update(score.0);
            if let Ok(mut score_text) = score_texts.p0().get_single_mut() {
                if let Some(section) = score_text.sections.first_mut() {
                    section.value = format!("SCORE: {:05}", score.0);
                }
            }
            if high_score.0 != previous_high_score {
                if let Ok(mut high_score_text) = score_texts.p1().get_single_mut() {
                    if let Some(section) = high_score_text.sections.first_mut() {
                        section.value = format!("HIGH SCORE: {:05}", high_score.0);
                    }
                }
            }
        }

        matched_pieces
            .iter()
            .filter_map(|coord| q_pieces.iter().find(|(_, piece)| piece.coord() == *coord))
            .for_each(|(entity, _)| {
                commands.entity(entity).despawn();
            });

        if !matched_pieces.is_empty() {
            // Commands are applied after this system. Validate again on the next frame.
            selection_info.request_game_over_check();
            continue;
        }

        match next_planned_move {
            NextPlannedMove::SpawnPieces => {
                if let Some(amount) = game_config.spawn_amount() {
                    spawn_new_pieces_event_writer.send(SpawnNewPiecesEvent::new(amount));
                }
            }
            NextPlannedMove::Play => {
                let occupied = piece_map.keys().copied().collect::<HashSet<_>>();
                if has_legal_move(&occupied) {
                    selection_info.start_choosing();
                } else {
                    show_game_over_event_writer.send(ShowGameOverEvent);
                }
            }
        }
    }
}

pub fn check_game_over(
    mut selection_info: ResMut<SelectionInfo>,
    q_pieces: Query<&Piece, With<Piece>>,
    mut show_game_over_event_writer: EventWriter<ShowGameOverEvent>,
) {
    if selection_info.is_game_over() || !selection_info.take_game_over_check() {
        return;
    }

    let occupied = q_pieces.iter().map(Piece::coord).collect::<HashSet<_>>();
    if has_legal_move(&occupied) {
        selection_info.start_choosing();
    } else {
        show_game_over_event_writer.send(ShowGameOverEvent);
    }
}
