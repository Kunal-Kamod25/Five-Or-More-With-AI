use bevy::prelude::{Camera, GlobalTransform, Vec2, Window};

pub fn screen_pos_to_world_pos(
    window: &Window,
    camera: &Camera,
    camera_transform: &GlobalTransform,
) -> Option<Vec2> {
    let screen_pos = window.cursor_position()?;

    camera.viewport_to_world_2d(camera_transform, screen_pos)
}
