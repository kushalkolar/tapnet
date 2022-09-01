# Copyright 2022 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Default config to train the TapNet."""
# import jax
from jaxline import base_config
from ml_collections import config_dict

from tapnet import kubric_task


# We define the experiment launch config in the same file as the experiment to
# keep things self-contained in a single file.
def get_config() -> config_dict.ConfigDict():  # pytype: disable=invalid-annotation
  """Return config object for training."""
  config = base_config.get_base_config()

  # Experiment config.
  config.training_steps = 500000

  # NOTE: duplicates not allowed.
  config.shared_module_names = ('tapnet_model',)

  config.dataset_names = (
      'kubric',
  )
  config.task_names = (
      'kubric',
  )
  # Note: eval modes must always start with 'eval_'.
  config.eval_modes = (
      'eval_kubric',
      'eval_jhmdb',
      'eval_robotics_points',
  )

  config.experiment_kwargs = config_dict.ConfigDict(
      dict(
          config=dict(
              sweep_name='default_sweep',
              save_final_checkpoint_as_npy=True,
              # `enable_double_transpose` should always be false when using 1D.
              # For other D It is also completely untested and very unlikely
              # to work.
              optimizer=dict(
                  base_lr=2e-3,
                  max_norm=-1,  # < 0 to turn off.
                  weight_decay=1e-2,
                  scale_by_batch=True,
                  schedule_type='cosine',
                  cosine_decay_kwargs=dict(
                      init_value=0.0,
                      warmup_steps=5000,
                      end_value=0.0,
                  ),
                  optimizer='adam',
                  # Optimizer-specific kwargs.
                  adam_kwargs=dict(
                      b1=0.9,
                      b2=0.95,
                      eps=1e-8,
                  ),
              ),
              fast_variables=('track_pred', 'rescaler_'),
              shared_modules=dict(
                  shared_module_names=config.get_oneway_ref(
                      'shared_module_names',),
                  tapnet_model_kwargs=dict()),
              datasets=dict(
                  dataset_names=config.get_oneway_ref('dataset_names'),
                  kubric_kwargs=dict(
                      batch_dims=4,
                      shuffle_buffer_size=128,
                      train_size=kubric_task.TRAIN_SIZE[1:3],
                  )),
              tasks=dict(
                  task_names=config.get_oneway_ref('task_names'),
                  kubric_kwargs=dict(prediction_algo='cost_volume_regressor'),
              ),
              training=dict(
                  # Note: to sweep n_training_steps, DO NOT sweep these
                  # fields directly. Instead sweep config.training_steps.
                  # Otherwise, decay/stopping logic
                  # is not guaranteed to be consistent.
                  n_training_steps=config.get_oneway_ref('training_steps'),))))

  # Set up where to store the resulting model.
  config.checkpoint_dir = 'checkpoints'
  config.train_checkpoint_all_hosts = False
  config.evaluate_every = 1000

  # If true, run evaluate() on the experiment once before
  # you load a checkpoint.
  # This is useful for getting initial values of metrics at random weights, or
  # when debugging locally if you do not have any train job running.
  config.eval_initial_weights = True
  config.jhmdb_path = None
  config.robotics_points_path = None
  # Prevents accidentally setting keys that aren't recognized (e.g. in tests).
  config.lock()

  return config