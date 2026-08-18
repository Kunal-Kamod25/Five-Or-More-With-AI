use bevy::prelude::Component;

#[derive(Component)]
pub struct DifficultyMenu;

#[derive(Component)]
pub struct DifficultySelectionText;

#[derive(Component, Clone, Copy)]
pub enum DifficultyButton {
    Easy,
    Medium,
    Hard,
    Start,
}
