# Hardware and resource planning

The profile table in the README names the project's intended hardware ladder:

- tiny: CPU
- seed-0: one RTX 4090
- seed-1: two A100 40GB
- seed-2: four A100 80GB

These are planning targets only. No hardware benchmark has been run by this repository bootstrap, and no training-time, cost or tokens-per-second guarantee is implied.

Before any non-tiny run, produce a machine-specific fit report containing:
- GPU model, count, VRAM, driver and CUDA versions;
- exact parameter count and dtype;
- microbatch size, sequence length and gradient accumulation;
- estimated and measured parameter, gradient, optimizer and activation memory;
- attention implementation and peak temporary allocations;
- data-loader CPU/RAM/storage throughput;
- measured step time, tokens/second and utilization;
- checkpoint size, write time and available disk space.

A model that fits in parameter memory may still fail during forward/backward due to activations, optimizer states, temporary workspaces, fragmentation or communication buffers. The current implementation does not yet provide a validated hardware-fit estimator. Do not use rough parameter-only arithmetic as a launch decision.
