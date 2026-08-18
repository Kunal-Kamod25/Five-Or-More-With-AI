use bevy::app::AppExit;
use bevy::hierarchy::DespawnRecursiveExt;
use bevy::prelude::{
    Button, Changed, Commands, Entity, EventWriter, Interaction, Query, ResMut, Text, With,
};

use crate::components::{GameOverButton, GameOverOverlay, Piece, ScoreText};
use crate::events::ShowDifficultyMenuEvent;
use crate::resources::{GameConfig, Score, SelectionInfo};

pub fn game_over_actions(
    mut commands: Commands,
    mut interactions: Query<(&Interaction, &GameOverButton), (Changed<Interaction>, With<Button>)>,
    overlays: Query<Entity, With<GameOverOverlay>>,
    pieces: Query<Entity, With<Piece>>,
    mut score_text: Query<&mut Text, With<ScoreText>>,
    mut score: ResMut<Score>,
    mut selection_info: ResMut<SelectionInfo>,
    mut difficulty_menu_writer: EventWriter<ShowDifficultyMenuEvent>,
    mut exit_writer: EventWriter<AppExit>,
    mut game_config: ResMut<GameConfig>,
) {
    for (interaction, button) in &mut interactions {
        if *interaction != Interaction::Pressed {
            continue;
        }

        match button {
            GameOverButton::Restart => {
                for overlay in &overlays {
                    commands.entity(overlay).despawn_recursive();
                }
                for piece in &pieces {
                    commands.entity(piece).despawn_recursive();
                }

                score.reset();
                if let Ok(mut text) = score_text.get_single_mut() {
                    if let Some(section) = text.sections.first_mut() {
                        section.value = "Score: 0".to_string();
                    }
                }
                selection_info.start_difficulty_selection();
                game_config.clear_difficulty();
                difficulty_menu_writer.send(ShowDifficultyMenuEvent);
            }
            GameOverButton::Quit => {
                exit_writer.send(AppExit);
            }
        }
    }
}
