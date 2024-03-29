print("importing stuff")
import os
from datetime import datetime

import gym
import vizdoomgym
import numpy as np
import skimage as skimage
from skimage import transform, color, exposure

print("importing DDQN")
from models.DDQN import DoubleDQNAgent

NUM_STEPS     = 5000

EPSILON = 0.9
EPSILON_DECAY = 0.99

convergence_count = 0

def preprocessImg(img, size):
    img = np.rollaxis(img, 0, 3)
    img = skimage.transform.resize(img, size)
    img = skimage.color.rgb2gray(img)

    return img

if __name__ == '__main__':


    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - beginning code")
    img_rows, img_cols = 64, 64
    # Convert image into Black and white
    img_channels = 4 # We stack 4 frames

    state_size = (img_rows, img_cols, img_channels)

    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - setting directory")
    os.chdir('/nfs')
    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - creating environment")
    env = gym.make('VizdoomTakeCover-v0')
    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - creating agent")
    agent = DoubleDQNAgent(state_size, env.action_space.n)

    episode = 0
    total_reward = 0
    average_reward = 0
    last_average = 0
    episode_rewards = []
    logs = []
    total_t_step = 0

    print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Environment and Agent intialized. Beginning game...")
    # print(f"{os.getcwd()}/WorldModelsExperiments/models/ddqn.h5", os.path.exists(f"{os.getcwd()}/WorldModelsExperiments/models/ddqn.h5"))

    while True:

        episode += 1
        episode_reward = 0
        state = env.reset()


    
        for t_step in range(NUM_STEPS):
            total_t_step += 1
            x_t = preprocessImg(state, size=(img_rows, img_cols))
            s_t = np.stack(([x_t]*4), axis=2) # It becomes 64x64x4
            s_t = np.expand_dims(s_t, axis=0) # 1x64x64x4

            action_idx = agent.get_action(s_t)
            try:
                next_state, reward, done, info = env.step(action_idx)
            except:
                print("VizDoom crashed. Rebooting.")
                break

            x_t1 = preprocessImg(next_state, size=(img_rows, img_cols))
            x_t1 = np.reshape(x_t1, (1, img_rows, img_cols, 1))
            s_t1 = np.append(x_t1, s_t[:, :, :, :3], axis=3)
            agent.replay_memory(s_t, action_idx, reward, s_t1, done, total_t_step)

            if total_t_step > agent.observe and total_t_step % agent.timestep_per_train == 0:
                Q_max, loss = agent.train_replay()
            
            state = next_state

            episode_reward += reward

            if t_step == NUM_STEPS or done:
                total_reward += episode_reward
                episode_rewards.append(episode_reward)
                break
        
        if episode%10 == 0:
            agent.save_model("ddqn.h5")

        if len(episode_rewards) > 1:
            average_reward = np.mean(episode_rewards[:-1])
        
        if (episode-1)%10 == 0:
            print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Episode {episode}:\n\tlatest episode reward: {episode_reward}\n\ttotal episode reward: {total_reward}\n\taverage_reward: {average_reward}\n\tchange in average:{average_reward-last_average}")
        logs.append(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Episode {episode}:\n\tlatest episode reward: {episode_reward}\n\ttotal episode reward: {total_reward}\n\taverage_reward: {average_reward}\n\tchange in average:{average_reward-last_average}")

        if episode != 1 and abs(average_reward - last_average) < .0001:
            if convergence_count < 5:
                print(f"Convergence count upped! Current count {convergence_count+1}")
                convergence_count += 1
            else:
                print('Converged! Ending sequence.')
                break
        else:
            convergence_count = 0

        last_average = average_reward

    agent.save_model("ddqn.h5")
    with open("run_ddqn_out.txt", "w+") as file:
        for log in logs:
            file.write(log + '\n')