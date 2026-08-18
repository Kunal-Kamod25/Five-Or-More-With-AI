use bevy::prelude::Component;

#[derive(Component)]
pub struct GameOverOverlay;

#[derive(Component)]
pub enum GameOverButton {
    Restart,
    Quit,
}
