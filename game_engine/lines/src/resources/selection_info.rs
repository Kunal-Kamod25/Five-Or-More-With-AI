use crate::constants::Coord;
use bevy::prelude::{Entity, Resource, Vec2};
use std::cmp::PartialEq;

#[derive(Debug, PartialEq)]
pub enum GameState {
    DifficultySelection,
    ChoosingPiece,
    MovingPiece,
    ValidatingMove,
    GameOver,
}

#[derive(Resource)]
pub struct SelectionInfo {
    entity: Option<Entity>,
    path: Vec<Vec2>,
    state: GameState,
    dest_coord: Option<Coord>,
    needs_game_over_check: bool,
}

#[cfg(test)]
mod tests {
    use super::SelectionInfo;
    use bevy::prelude::Entity;

    #[test]
    fn game_over_clears_pending_interaction_state() {
        let mut selection_info = SelectionInfo::new();
        selection_info.select(Entity::from_raw(1));
        selection_info.set_path(vec![bevy::prelude::Vec2::ZERO]);
        selection_info.set_dest_coord((2, 2));

        selection_info.set_game_over();

        assert!(selection_info.is_game_over());
        assert!(selection_info.selected().is_none());
        assert!(selection_info.empty_path());
        assert!(selection_info.pop_dest_coord().is_none());
    }
}

impl SelectionInfo {
    pub fn new() -> Self {
        Self {
            entity: None,
            path: vec![],
            state: GameState::ChoosingPiece,
            dest_coord: None,
            needs_game_over_check: false,
        }
    }

    pub fn selected(&self) -> Option<Entity> {
        self.entity
    }

    pub fn select(&mut self, entity: Entity) {
        self.entity = Some(entity);
    }

    pub fn deselect(&mut self) {
        self.entity = None;
    }

    pub fn set_path(&mut self, path: Vec<Vec2>) {
        self.path = path;
    }

    pub fn get_path(&self) -> Vec<Vec2> {
        self.path.clone()
    }

    pub fn pop_path(&mut self) {
        if !self.path.is_empty() {
            self.path.remove(0);
        }
    }

    pub fn empty_path(&self) -> bool {
        self.path.is_empty()
    }

    pub fn start_choosing(&mut self) {
        self.state = GameState::ChoosingPiece;
    }

    pub fn start_new_game(&mut self) {
        self.entity = None;
        self.path.clear();
        self.dest_coord = None;
        self.needs_game_over_check = false;
        self.state = GameState::ChoosingPiece;
    }

    pub fn start_difficulty_selection(&mut self) {
        self.entity = None;
        self.path.clear();
        self.dest_coord = None;
        self.needs_game_over_check = false;
        self.state = GameState::DifficultySelection;
    }

    pub fn is_choosing(&self) -> bool {
        self.state == GameState::ChoosingPiece
    }

    pub fn start_moving(&mut self) {
        self.state = GameState::MovingPiece;
    }

    pub fn is_moving(&self) -> bool {
        self.state == GameState::MovingPiece
    }

    pub fn validate_move(&mut self) {
        self.state = GameState::ValidatingMove;
    }

    pub fn set_game_over(&mut self) {
        self.entity = None;
        self.path.clear();
        self.dest_coord = None;
        self.needs_game_over_check = false;
        self.state = GameState::GameOver;
    }

    pub fn is_game_over(&self) -> bool {
        self.state == GameState::GameOver
    }

    pub fn request_game_over_check(&mut self) {
        self.needs_game_over_check = true;
    }

    pub fn take_game_over_check(&mut self) -> bool {
        std::mem::take(&mut self.needs_game_over_check)
    }

    pub fn set_dest_coord(&mut self, coord: Coord) {
        self.dest_coord = Some(coord);
    }

    pub fn pop_dest_coord(&mut self) -> Option<Coord> {
        if self.dest_coord.is_none() {
            return None;
        }
        self.dest_coord.take()
    }
}
