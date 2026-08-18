use bevy::asset::AssetServer;
use bevy::prelude::{default, Commands, PositionType, Res, Style, TextBundle, TextStyle, Val};

use crate::components::{HighScoreText, ScoreText};

pub fn spawn_score(mut commands: Commands, asset_server: Res<AssetServer>) {
    commands.spawn((
        TextBundle::from_section(
            "SCORE: 00000",
            TextStyle {
                font: asset_server.load("fonts/AmericanCaptain.ttf"),
                font_size: 30.0,
                ..default()
            },
        )
        .with_style(Style {
            position_type: PositionType::Absolute,
            top: Val::Px(10.0),
            left: Val::Px(10.0),
            ..default()
        }),
        ScoreText,
    ));

    commands.spawn((
        TextBundle::from_section(
            "HI: 00000",
            TextStyle {
                font: asset_server.load("fonts/AmericanCaptain.ttf"),
                font_size: 30.0,
                ..default()
            },
        )
        .with_style(Style {
            position_type: PositionType::Absolute,
            top: Val::Px(10.0),
            right: Val::Px(10.0),
            ..default()
        }),
        HighScoreText,
    ));
}
