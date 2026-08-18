use bevy::asset::AssetServer;
use bevy::hierarchy::{BuildChildren, DespawnRecursiveExt};
use bevy::prelude::{
    AlignItems, BackgroundColor, Button, ButtonBundle, Color, Commands, Entity, EventReader,
    EventWriter, FlexDirection, Interaction, JustifyContent, NodeBundle, Query, Res, ResMut, Style,
    Text, TextBundle, TextStyle, UiRect, Val, With,
};

use crate::components::{DifficultyButton, DifficultyMenu, DifficultySelectionText};
use crate::events::{ShowDifficultyMenuEvent, SpawnNewPiecesEvent};
use crate::resources::{Difficulty, GameConfig, SelectionInfo};

const INITIAL_PIECES: usize = 5;

pub fn spawn_difficulty_menu(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    mut selection_info: ResMut<SelectionInfo>,
    mut config: ResMut<GameConfig>,
) {
    selection_info.start_difficulty_selection();
    config.clear_difficulty();
    spawn_menu(&mut commands, &asset_server);
}

pub fn show_difficulty_menu(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    mut events: EventReader<ShowDifficultyMenuEvent>,
    menus: Query<Entity, With<DifficultyMenu>>,
    mut selection_info: ResMut<SelectionInfo>,
    mut config: ResMut<GameConfig>,
) {
    if events.read().next().is_none() || !menus.is_empty() {
        return;
    }

    selection_info.start_difficulty_selection();
    config.clear_difficulty();
    spawn_menu(&mut commands, &asset_server);
}

pub fn difficulty_menu_actions(
    mut commands: Commands,
    mut buttons: Query<(&Interaction, &DifficultyButton, &mut BackgroundColor), With<Button>>,
    menus: Query<Entity, With<DifficultyMenu>>,
    mut selection_text: Query<&mut Text, With<DifficultySelectionText>>,
    mut config: ResMut<GameConfig>,
    mut selection_info: ResMut<SelectionInfo>,
    mut spawn_writer: EventWriter<SpawnNewPiecesEvent>,
) {
    let mut start_requested = false;
    let mut selected_difficulty = config.difficulty();

    for (interaction, button, _) in &mut buttons {
        if *interaction != Interaction::Pressed {
            continue;
        }

        match button {
            DifficultyButton::Easy => {
                selected_difficulty = Some(Difficulty::Easy);
            }
            DifficultyButton::Medium => {
                selected_difficulty = Some(Difficulty::Medium);
            }
            DifficultyButton::Hard => {
                selected_difficulty = Some(Difficulty::Hard);
            }
            DifficultyButton::Start => start_requested = true,
        }
    }

    if let Some(difficulty) = selected_difficulty {
        if config.difficulty() != Some(difficulty) {
            config.set_difficulty(difficulty);
            update_selection_text(&mut selection_text, difficulty);
        }
    }

    for (_, button, mut background) in &mut buttons {
        let is_selected = match button {
            DifficultyButton::Easy => selected_difficulty == Some(Difficulty::Easy),
            DifficultyButton::Medium => selected_difficulty == Some(Difficulty::Medium),
            DifficultyButton::Hard => selected_difficulty == Some(Difficulty::Hard),
            DifficultyButton::Start => false,
        };
        background.0 = if is_selected {
            Color::rgb(0.15, 0.7, 0.3)
        } else {
            Color::rgb(0.2, 0.2, 0.2)
        };
    }

    if !start_requested || config.difficulty().is_none() {
        return;
    }

    for menu in &menus {
        commands.entity(menu).despawn_recursive();
    }
    selection_info.start_new_game();
    spawn_writer.send(SpawnNewPiecesEvent::new(INITIAL_PIECES));
}

fn update_selection_text(
    selection_text: &mut Query<&mut Text, With<DifficultySelectionText>>,
    difficulty: Difficulty,
) {
    if let Ok(mut text) = selection_text.get_single_mut() {
        if let Some(section) = text.sections.first_mut() {
            section.value = format!("Selected: {}", difficulty.label());
        }
    }
}

fn spawn_menu(commands: &mut Commands, asset_server: &AssetServer) {
    commands
        .spawn((
            NodeBundle {
                style: Style {
                    width: Val::Percent(100.0),
                    height: Val::Percent(100.0),
                    justify_content: JustifyContent::Center,
                    align_items: AlignItems::Center,
                    flex_direction: FlexDirection::Column,
                    ..Default::default()
                },
                background_color: Color::BLACK.with_a(0.5).into(),
                ..Default::default()
            },
            DifficultyMenu,
        ))
        .with_children(|parent| {
            parent.spawn(TextBundle::from_section(
                "Choose Difficulty",
                TextStyle {
                    font: asset_server.load("fonts/AmericanCaptain.ttf"),
                    font_size: 100.0,
                    color: Color::WHITE,
                },
            ));

            parent.spawn((
                TextBundle::from_section(
                    "Selected: Choose a difficulty",
                    TextStyle {
                        font: asset_server.load("fonts/AmericanCaptain.ttf"),
                        font_size: 42.0,
                        color: Color::WHITE,
                    },
                ),
                DifficultySelectionText,
            ));

            spawn_difficulty_button(parent, asset_server, DifficultyButton::Easy, "Easy");
            spawn_difficulty_button(parent, asset_server, DifficultyButton::Medium, "Medium");
            spawn_difficulty_button(parent, asset_server, DifficultyButton::Hard, "Hard");
            spawn_difficulty_button(parent, asset_server, DifficultyButton::Start, "Start Game");
        });
}

fn spawn_difficulty_button(
    parent: &mut bevy::hierarchy::ChildBuilder,
    asset_server: &AssetServer,
    difficulty: DifficultyButton,
    label: &str,
) {
    parent
        .spawn((
            ButtonBundle {
                style: Style {
                    width: Val::Px(280.0),
                    height: Val::Px(58.0),
                    margin: UiRect::all(Val::Px(6.0)),
                    justify_content: JustifyContent::Center,
                    align_items: AlignItems::Center,
                    ..Default::default()
                },
                background_color: Color::rgb(0.2, 0.2, 0.2).into(),
                ..Default::default()
            },
            difficulty,
        ))
        .with_children(|button| {
            button.spawn(TextBundle::from_section(
                label,
                TextStyle {
                    font: asset_server.load("fonts/AmericanCaptain.ttf"),
                    font_size: 38.0,
                    color: Color::WHITE,
                },
            ));
        });
}
