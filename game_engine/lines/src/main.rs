use crate::event_handlers::{
    calculate_movement_path_event_handler, center_piece_to_tile_event_handler, check_game_over,
    show_game_over_event_hander, spawn_new_pieces_event_handler, validate_move_event_handler,
};
use crate::events::{
    CalculateMovementPathEvent, CenterPieceToTileEvent, ShowDifficultyMenuEvent, ShowGameOverEvent,
    SpawnNewPiecesEvent, ValidateMoveEvent,
};
use crate::systems::{
    animate_selected_piece, difficulty_menu_actions, game_over_actions, move_pieces, select_piece,
    show_difficulty_menu, spawn_board, spawn_camera, spawn_difficulty_menu, spawn_score,
};
use bevy::prelude::{App, FixedUpdate, IntoSystemConfigs, PreStartup, Update};
use bevy::DefaultPlugins;
use bevy_prototype_lyon::prelude::ShapePlugin;

mod actions;
mod components;
mod constants;
mod event_handlers;
mod events;
mod game_logic;
mod resources;
mod systems;
mod types;

fn main() {
    App::new()
        .add_plugins(DefaultPlugins)
        .add_plugins(ShapePlugin)
        .add_event::<ValidateMoveEvent>()
        .add_event::<SpawnNewPiecesEvent>()
        .add_event::<ShowGameOverEvent>()
        .add_event::<ShowDifficultyMenuEvent>()
        .add_event::<CenterPieceToTileEvent>()
        .add_event::<CalculateMovementPathEvent>()
        .add_systems(
            Update,
            (
                check_game_over,
                validate_move_event_handler,
                spawn_new_pieces_event_handler,
                show_game_over_event_hander,
                center_piece_to_tile_event_handler,
                calculate_movement_path_event_handler,
            )
                .chain(),
        )
        .insert_resource(resources::Score::new())
        .insert_resource(resources::SelectionInfo::new())
        .add_systems(
            PreStartup,
            (
                spawn_camera,
                spawn_score,
                spawn_board,
                spawn_difficulty_menu,
            )
                .chain(),
        )
        .add_systems(Update, select_piece)
        .add_systems(
            Update,
            (
                game_over_actions,
                show_difficulty_menu,
                difficulty_menu_actions,
            )
                .chain(),
        )
        .insert_resource(resources::GameConfig::new())
        .insert_resource(resources::HighScore::new())
        .add_systems(FixedUpdate, (move_pieces, animate_selected_piece))
        .run();
}
