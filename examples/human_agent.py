# Copyright 2020 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Example human agent for interacting with DeepMind Hard Eight Tasks."""

from absl import app
from absl import flags
from absl import logging
import dm_hard_eight
import numpy as np
import pygame

FLAGS = flags.FLAGS

flags.DEFINE_list(
    'screen_size', [640, 480],
    'Screen width/height in pixels. Scales the environment RGB observations to '
    'fit the screen size.')

flags.DEFINE_string(
    'docker_image_name', None,
    'Name of the Docker image that contains the Hard Eight Tasks. '
    'If None, uses the default dm_hard_eight image name')

flags.DEFINE_integer('seed', 123, 'Environment seed.')
flags.DEFINE_string('level_name', 'ball_room_navigation_cubes',
                    'Name of Hard Eight task to run.')

_FRAMES_PER_SECOND = 30
_MOUSE_SENSITIVITY = 0.1

_CURSOR_COLOR = (255, 0, 0)
_CURSOR_SIZE = 2

_LEFT_BUTTON = 1

_KEYS_TO_ACTION = {
    pygame.K_w: {'MOVE_BACK_FORWARD': 1},
    pygame.K_s: {'MOVE_BACK_FORWARD': -1},
    pygame.K_a: {'STRAFE_LEFT_RIGHT': -1},
    pygame.K_d: {'STRAFE_LEFT_RIGHT': 1},
    pygame.K_UP: {'LOOK_DOWN_UP': -1},
    pygame.K_DOWN: {'LOOK_DOWN_UP': 1},
    pygame.K_LEFT: {'LOOK_LEFT_RIGHT': -1},
    pygame.K_RIGHT: {'LOOK_LEFT_RIGHT': 1},
    pygame.K_i: {'LOOK_DOWN_UP': -1},
    pygame.K_k: {'LOOK_DOWN_UP': 1},
    pygame.K_j: {'LOOK_LEFT_RIGHT': -1},
    pygame.K_l: {'LOOK_LEFT_RIGHT': 1},
    pygame.K_y: {'HAND_ROTATE_AROUND_FORWARD': 1},
    pygame.K_r: {'HAND_ROTATE_AROUND_FORWARD': -1},
    pygame.K_t: {'HAND_ROTATE_AROUND_RIGHT': -1},
    pygame.K_g: {'HAND_ROTATE_AROUND_RIGHT': 1},
    pygame.K_f: {'HAND_ROTATE_AROUND_UP': -1},
    pygame.K_h: {'HAND_ROTATE_AROUND_UP': 1},
    pygame.K_b: {'HAND_PUSH_PULL': 10},
    pygame.K_v: {'HAND_PUSH_PULL': -10},
    pygame.K_SPACE: {'HAND_GRIP': 1},
}  # pyformat: disable

_NO_ACTION = {
    'MOVE_BACK_FORWARD': 0,
    'STRAFE_LEFT_RIGHT': 0,
    'LOOK_LEFT_RIGHT': 0,
    'LOOK_DOWN_UP': 0,
    'HAND_ROTATE_AROUND_FORWARD': 0,
    'HAND_ROTATE_AROUND_RIGHT': 0,
    'HAND_ROTATE_AROUND_UP': 0,
    'HAND_PUSH_PULL': 0,
    'HAND_GRIP': 0
}


def _grab_mouse(grab=True):
  pygame.event.set_grab(grab)
  pygame.mouse.set_visible(not grab)


def main(_):
  pygame.init()
  try:
    pygame.mixer.quit()
  except NotImplementedError:
    pass
  pygame.display.set_caption('Hard Eight Human Agent')

  env_settings = dm_hard_eight.EnvironmentSettings(
      seed=FLAGS.seed, level_name=FLAGS.level_name)
  with dm_hard_eight.load_from_docker(name=FLAGS.docker_image_name,
                                      settings=env_settings) as env:
    screen = pygame.display.set_mode(
        (int(FLAGS.screen_size[0]), int(FLAGS.screen_size[1])))

    rgb_spec = env.observation_spec()['RGB_INTERLEAVED']
    surface = pygame.Surface((rgb_spec.shape[1], rgb_spec.shape[0]))

    score = 0
    clock = pygame.time.Clock()
    while True:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          return
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_q:
            return
          if event.key == pygame.K_ESCAPE:
            _grab_mouse(not pygame.event.get_grab())
        elif event.type == pygame.MOUSEBUTTONDOWN:
          if event.button == _LEFT_BUTTON:
            _grab_mouse()

      actions = _NO_ACTION.copy()

      keys = pygame.key.get_pressed()
      for key, key_actions in _KEYS_TO_ACTION.items():
        if not keys[key]:
          continue
        for name, action in key_actions.items():
          actions[name] = action

      if pygame.event.get_grab():
        left_button_pressed, _, _ = pygame.mouse.get_pressed()
        if left_button_pressed:
          actions['HAND_GRIP'] = 1

        x, y = pygame.mouse.get_rel()
        actions['LOOK_LEFT_RIGHT'] = _MOUSE_SENSITIVITY * x
        actions['LOOK_DOWN_UP'] = _MOUSE_SENSITIVITY * y

      timestep = env.step(actions)
      frame = np.swapaxes(timestep.observation['RGB_INTERLEAVED'], 0, 1)
      pygame.surfarray.blit_array(surface, frame)
      pygame.transform.smoothscale(surface, screen.get_size(), screen)

      info = pygame.display.Info()
      rect_x = (info.current_w  - _CURSOR_SIZE) // 2
      rect_y = (info.current_h - _CURSOR_SIZE) // 2
      fill_rectangle = 0
      pygame.draw.rect(screen, _CURSOR_COLOR,
                       (rect_x, rect_y, _CURSOR_SIZE, _CURSOR_SIZE),
                       fill_rectangle)

      pygame.display.update()

      if timestep.reward:
        score += timestep.reward
        logging.info('Total score: %1.1f, reward: %1.1f', score,
                     timestep.reward)
      clock.tick(_FRAMES_PER_SECOND)


if __name__ == '__main__':
  app.run(main)
