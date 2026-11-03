# Training operations

The trainer is shared by every model profile. Profile configuration changes model dimensions and resource settings; it must not select a separate training implementation.

## Implemented bootstrap behavior

- AdamW optimizer.
- Linear warmup followed by cosine decay to a configured minimum learning rate.
- Gradient accumulation and global gradient clipping.
- Runtime precision selection: BF16 on supported CUDA devices, otherwise FP16 on CUDA, FP32 on CPU. Explicit unsupported precision requests fail loudly.
- Non-finite loss and gradient-norm detection.
- Periodic atomic checkpoint writes containing model, optimizer, scaler, step, Python/NumPy/CPU/CUDA RNG and the next-token sampler generator state.
- Resume from a checkpoint with strict training-config equality; the closed-form learning-rate schedule is reconstructed from the global step.

Resume currently supports the deterministic next-token batch sampler. A future streaming/distributed data loader must provide its own serializable cursor/state before it can claim exact resume semantics.

## Required next steps

- Add validation loop and best-checkpoint selection.
- Add GradScaler overflow/skipped-step telemetry.
- Add activation checkpointing and distributed data/model parallel strategies.
- Add loss-spike detection, diagnostics and bounded recovery. Never silently roll back weights without recording the event.
- Add early stopping only for explicitly configured finite-data experiments; it must not silently terminate long pretraining runs.
- Add checkpoint rotation, disk-space safeguards and signal-safe shutdown.
- Record tokens seen, tokens/sec, optimizer steps, effective batch size, gradient norm, learning rate, precision and hardware.
- Persist the exact resolved config and data/tokenizer fingerprints with every run.

## Operational safety

Hardware-fit and cost calculations must be labelled estimates until benchmarked on the target host. Account for parameters, gradients, optimizer states, activations, temporary attention buffers, fragmentation and distributed communication. A simplistic parameter-only estimate is not a fit guarantee.
