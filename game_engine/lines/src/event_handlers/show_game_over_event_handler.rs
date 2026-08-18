use bevy::asset::AssetServer;
use bevy::hierarchy::BuildChildren;
use bevy::prelude::{
    AlignItems, ButtonBundle, Color, Commands, EventReader, FlexDirection, JustifyContent,
    NodeBundle, Res, ResMut, Style, TextBundle, TextStyle, UiRect, Val,
};

use crate::components::{GameOverButton, GameOverOverlay};
use crate::events::ShowGameOverEvent;
use crate::resources::{HighScore, Score, SelectionInfo};

pub fn show_game_over_event_hander(
    mut commands: Commands,
    asset_server: Res<AssetServer>,
    score: Res<Score>,
    high_score: Res<HighScore>,
    mut selection_info: ResMut<SelectionInfo>,
    mut show_game_over_event_reader: EventReader<ShowGameOverEvent>,
) {
    for _ in show_game_over_event_reader.read() {
        if selection_info.is_game_over() {
            continue;
        }

        selection_info.set_game_over();

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
                GameOverOverlay,
            ))
            .with_children(|parent| {
                parent.spawn(TextBundle::from_section(
                    "Game Over!",
                    TextStyle {
                        font: asset_server.load("fonts/AmericanCaptain.ttf"),
                        font_size: 200.0,
                        color: Color::WHITE,
                    },
                ));

                parent.spawn(TextBundle::from_section(
                    &format!("Score: {}", score.0),
                    TextStyle {
                        font: asset_server.load("fonts/AmericanCaptain.ttf"),
                        font_size: 100.0,
                        color: Color::WHITE,
                    },
                ));

                parent.spawn(TextBundle::from_section(
                    &format!("Session High Score: {}", high_score.0),
                    TextStyle {
                        font: asset_server.load("fonts/AmericanCaptain.ttf"),
                        font_size: 70.0,
                        color: Color::GOLD,
                    },
                ));

                parent
                    .spawn((
                        ButtonBundle {
                            style: Style {
                                width: Val::Px(260.0),
                                height: Val::Px(64.0),
                                margin: UiRect::all(Val::Px(8.0)),
                                justify_content: JustifyContent::Center,
                                align_items: AlignItems::Center,
                                ..Default::default()
                            },
                            background_color: Color::rgb(0.1, 0.55, 0.25).into(),
                            ..Default::default()
                        },
                        GameOverButton::Restart,
                    ))
                    .with_children(|button| {
                        button.spawn(TextBundle::from_section(
                            "Start New Game",
                            TextStyle {
                                font: asset_server.load("fonts/AmericanCaptain.ttf"),
                                font_size: 42.0,
                                color: Color::WHITE,
                            },
                        ));
                    });

                parent
                    .spawn((
                        ButtonBundle {
                            style: Style {
                                width: Val::Px(260.0),
                                height: Val::Px(64.0),
                                margin: UiRect::all(Val::Px(8.0)),
                                justify_content: JustifyContent::Center,
                                align_items: AlignItems::Center,
                                ..Default::default()
                            },
                            background_color: Color::rgb(0.65, 0.12, 0.12).into(),
                            ..Default::default()
                        },
                        GameOverButton::Quit,
                    ))
                    .with_children(|button| {
                        button.spawn(TextBundle::from_section(
                            "Quit",
                            TextStyle {
                                font: asset_server.load("fonts/AmericanCaptain.ttf"),
                                font_size: 42.0,
                                color: Color::WHITE,
                            },
                        ));
                    });
            });
    }
}
