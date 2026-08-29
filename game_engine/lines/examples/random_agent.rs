use lines::rl::{evaluate_random_agent, EnvironmentConfig};

fn main() {
    let stats = evaluate_random_agent(1_000, EnvironmentConfig::default(), 2026)
        .expect("random-agent evaluation failed");

    println!("Random Agent Evaluation");
    println!("=======================");
    println!("Episodes:              {}", stats.episodes);
    println!("Total steps:           {}", stats.total_steps);
    println!("Average score:         {:.2}", stats.average_score());
    println!("Highest score:         {}", stats.highest_score);
    println!("Lowest score:          {}", stats.lowest_score);
    println!(
        "Average episode length: {:.2}",
        stats.average_episode_length()
    );
    println!("Longest episode:       {}", stats.longest_episode);
    println!("Shortest episode:      {}", stats.shortest_episode);
    println!("Game-over episodes:    {}", stats.game_over_episodes);
    println!("Truncated episodes:    {}", stats.truncated_episodes);
    println!("Average reward:        {:.2}", stats.average_reward());
    println!("Highest total reward:  {:.2}", stats.highest_total_reward);
    println!("Lowest total reward:   {:.2}", stats.lowest_total_reward);
    println!(
        "Simulation time:       {:.2} seconds",
        stats.simulation_time.as_secs_f64()
    );
    println!("Steps/second:          {:.0}", stats.steps_per_second());
}
