#!/usr/bin/env python3
"""
InvokeAI Image Generation Script

Generates images via InvokeAI's REST API using node-based graphs.
Supports FLUX.2 Klein, Z-Image Turbo, FLUX.1, and SDXL models.

Environment Variables:
    INVOKEAI_API_URL: Base URL (default: http://localhost:9090)
    INVOKEAI_AUTH_TOKEN: Optional auth token for remote instances

Usage:
    python generate.py --prompt "a sunset over mountains" [options]
    python generate.py --list-models
    python generate.py --model-info MODEL_KEY
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# Environment configuration
API_URL = os.environ.get("INVOKEAI_API_URL", "http://localhost:9090")
AUTH_TOKEN = os.environ.get("INVOKEAI_AUTH_TOKEN")


def check_env() -> bool:
    """Check environment configuration and print current settings."""
    if not os.environ.get("INVOKEAI_API_URL"):
        print(f"Note: Using default API URL: {API_URL}", file=sys.stderr)
        print("Set INVOKEAI_API_URL to override, e.g.:", file=sys.stderr)
        print("  export INVOKEAI_API_URL='http://localhost:9090'", file=sys.stderr)
        print("  export INVOKEAI_AUTH_TOKEN='your-token'  # optional\n", file=sys.stderr)
    return True


def api_request(
    endpoint: str, method: str = "GET", data: dict | None = None, timeout: int = 30
) -> Any:
    """Make API request to InvokeAI."""
    url = f"{API_URL.rstrip('/')}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            if not body:
                return {}
            return json.loads(body)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}", file=sys.stderr)
        return None
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"API Error {e.code}: {body}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print(f"Is InvokeAI running at {API_URL}?", file=sys.stderr)
        return None


def download_file(endpoint: str, output_path: Path) -> bool:
    """Download a file from InvokeAI."""
    url = f"{API_URL.rstrip('/')}{endpoint}"
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            output_path.write_bytes(resp.read())
        return True
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"Download error: {e}", file=sys.stderr)
        return False


def list_models(model_type: str = "main", base_model: str | None = None) -> list[dict[str, Any]]:
    """List installed models."""
    params = [f"model_type={model_type}"]
    if base_model:
        params.append(f"base_models={base_model}")
    endpoint = f"/api/v2/models/?{'&'.join(params)}"
    result = api_request(endpoint)
    if isinstance(result, dict):
        return result.get("models", [])
    return []


def get_model_info(model_key: str) -> dict[str, Any] | None:
    """Get detailed model information."""
    result = api_request(f"/api/v2/models/i/{model_key}")
    return result if isinstance(result, dict) else None


def detect_model_type(model: dict[str, Any]) -> str:
    """Detect model architecture from model config."""
    base = model.get("base", "").lower()
    name = model.get("name", "").lower()

    # FLUX.2 Klein detection (includes GGUF variants)
    if "flux2" in base or "klein" in name:
        return "flux2_klein"
    # Z-Image Turbo (SDXL-based turbo model)
    if "z-image" in name or "zimage" in name:
        return "sdxl_turbo"
    # Standard FLUX.1
    if "flux" in base:
        return "flux"
    # SDXL (including turbo/lightning variants)
    if "sdxl" in base:
        if "turbo" in name or "lightning" in name:
            return "sdxl_turbo"
        return "sdxl"
    # Default to SDXL for unknown models
    return "sdxl"


def build_flux2_klein_graph(
    model: dict[str, Any],
    prompt: str,
    width: int,
    height: int,
    steps: int,
    seed: int,
) -> dict[str, Any]:
    """Build FLUX.2 Klein text-to-image graph."""
    model_key = model["key"]
    model_hash = model.get("hash", "")

    return {
        "id": f"flux2-klein-{int(time.time())}",
        "nodes": {
            "model_loader": {
                "id": "model_loader",
                "type": "flux2_klein_model_loader",
                "model": {
                    "key": model_key,
                    "hash": model_hash,
                    "name": model.get("name", ""),
                    "base": model.get("base", "flux2"),
                    "type": "main",
                },
                "qwen3_source_model": {
                    "key": model_key,
                    "hash": model_hash,
                    "name": model.get("name", ""),
                    "base": model.get("base", "flux2"),
                    "type": "main",
                },
                "max_seq_len": 512,
                "is_intermediate": True,
            },
            "text_encoder": {
                "id": "text_encoder",
                "type": "flux2_klein_text_encoder",
                "prompt": prompt,
                "max_seq_len": 512,
                "is_intermediate": True,
            },
            "denoise": {
                "id": "denoise",
                "type": "flux2_denoise",
                "width": width,
                "height": height,
                "num_steps": steps,
                "cfg_scale": 1.0,
                "scheduler": "euler",
                "seed": seed,
                "is_intermediate": True,
            },
            "vae_decode": {
                "id": "vae_decode",
                "type": "flux2_vae_decode",
                "is_intermediate": False,
            },
        },
        "edges": [
            {"source": {"node_id": "model_loader", "field": "transformer"}, "destination": {"node_id": "denoise", "field": "transformer"}},
            {"source": {"node_id": "model_loader", "field": "vae"}, "destination": {"node_id": "denoise", "field": "vae"}},
            {"source": {"node_id": "model_loader", "field": "qwen3_encoder"}, "destination": {"node_id": "text_encoder", "field": "qwen3_encoder"}},
            {"source": {"node_id": "text_encoder", "field": "conditioning"}, "destination": {"node_id": "denoise", "field": "positive_text_conditioning"}},
            {"source": {"node_id": "denoise", "field": "latents"}, "destination": {"node_id": "vae_decode", "field": "latents"}},
            {"source": {"node_id": "model_loader", "field": "vae"}, "destination": {"node_id": "vae_decode", "field": "vae"}},
        ],
    }


def build_flux_graph(
    model: dict[str, Any],
    prompt: str,
    width: int,
    height: int,
    steps: int,
    seed: int,
) -> dict[str, Any]:
    """Build FLUX.1 text-to-image graph."""
    model_key = model["key"]

    return {
        "id": f"flux-{int(time.time())}",
        "nodes": {
            "model_loader": {
                "id": "model_loader",
                "type": "flux_model_loader",
                "model": {"key": model_key},
                "is_intermediate": True,
            },
            "text_encoder": {
                "id": "text_encoder",
                "type": "flux_text_encoder",
                "prompt": prompt,
                "is_intermediate": True,
            },
            "denoise": {
                "id": "denoise",
                "type": "flux_denoise",
                "num_steps": steps,
                "width": width,
                "height": height,
                "seed": seed,
                "is_intermediate": True,
            },
            "decode": {
                "id": "decode",
                "type": "flux_vae_decode",
                "is_intermediate": False,
            },
        },
        "edges": [
            {"source": {"node_id": "model_loader", "field": "transformer"}, "destination": {"node_id": "denoise", "field": "transformer"}},
            {"source": {"node_id": "model_loader", "field": "clip"}, "destination": {"node_id": "text_encoder", "field": "clip"}},
            {"source": {"node_id": "model_loader", "field": "t5_encoder"}, "destination": {"node_id": "text_encoder", "field": "t5_encoder"}},
            {"source": {"node_id": "text_encoder", "field": "conditioning"}, "destination": {"node_id": "denoise", "field": "positive_text_conditioning"}},
            {"source": {"node_id": "denoise", "field": "latents"}, "destination": {"node_id": "decode", "field": "latents"}},
            {"source": {"node_id": "model_loader", "field": "vae"}, "destination": {"node_id": "decode", "field": "vae"}},
        ],
    }


def build_sdxl_graph(
    model: dict[str, Any],
    prompt: str,
    negative: str,
    width: int,
    height: int,
    steps: int,
    cfg: float,
    scheduler: str,
    seed: int,
) -> dict[str, Any]:
    """Build SDXL text-to-image graph."""
    model_key = model["key"]

    return {
        "id": f"sdxl-{int(time.time())}",
        "nodes": {
            "model_loader": {
                "id": "model_loader",
                "type": "sdxl_model_loader",
                "model": {"key": model_key},
                "is_intermediate": True,
            },
            "pos_prompt": {
                "id": "pos_prompt",
                "type": "sdxl_compel_prompt",
                "prompt": prompt,
                "is_intermediate": True,
            },
            "neg_prompt": {
                "id": "neg_prompt",
                "type": "sdxl_compel_prompt",
                "prompt": negative,
                "is_intermediate": True,
            },
            "noise": {
                "id": "noise",
                "type": "noise",
                "seed": seed,
                "width": width,
                "height": height,
                "is_intermediate": True,
            },
            "denoise": {
                "id": "denoise",
                "type": "denoise_latents",
                "steps": steps,
                "cfg_scale": cfg,
                "scheduler": scheduler,
                "denoising_start": 0.0,
                "denoising_end": 1.0,
                "is_intermediate": True,
            },
            "decode": {
                "id": "decode",
                "type": "latents_to_image",
                "is_intermediate": False,
            },
        },
        "edges": [
            {"source": {"node_id": "model_loader", "field": "unet"}, "destination": {"node_id": "denoise", "field": "unet"}},
            {"source": {"node_id": "model_loader", "field": "clip"}, "destination": {"node_id": "pos_prompt", "field": "clip"}},
            {"source": {"node_id": "model_loader", "field": "clip2"}, "destination": {"node_id": "pos_prompt", "field": "clip2"}},
            {"source": {"node_id": "model_loader", "field": "clip"}, "destination": {"node_id": "neg_prompt", "field": "clip"}},
            {"source": {"node_id": "model_loader", "field": "clip2"}, "destination": {"node_id": "neg_prompt", "field": "clip2"}},
            {"source": {"node_id": "pos_prompt", "field": "conditioning"}, "destination": {"node_id": "denoise", "field": "positive_conditioning"}},
            {"source": {"node_id": "neg_prompt", "field": "conditioning"}, "destination": {"node_id": "denoise", "field": "negative_conditioning"}},
            {"source": {"node_id": "noise", "field": "noise"}, "destination": {"node_id": "denoise", "field": "noise"}},
            {"source": {"node_id": "denoise", "field": "latents"}, "destination": {"node_id": "decode", "field": "latents"}},
            {"source": {"node_id": "model_loader", "field": "vae"}, "destination": {"node_id": "decode", "field": "vae"}},
        ],
    }


# Model type -> default parameters (based on community research)
MODEL_DEFAULTS: dict[str, dict[str, Any]] = {
    "flux2_klein": {"width": 1024, "height": 1024, "steps": 4, "cfg": 1.0, "scheduler": "euler"},
    "sdxl_turbo": {"width": 1024, "height": 1024, "steps": 8, "cfg": 1.0, "scheduler": "dpmpp_sde"},
    "flux": {"width": 1024, "height": 1024, "steps": 25, "cfg": 1.0, "scheduler": "euler"},
    "sdxl": {"width": 1024, "height": 1024, "steps": 25, "cfg": 6.0, "scheduler": "dpmpp_2m_k"},
}


def get_defaults_for_model(model_type: str) -> dict[str, Any]:
    """Get recommended defaults based on model architecture."""
    return MODEL_DEFAULTS.get(model_type, MODEL_DEFAULTS["sdxl"])


def enqueue_generation(graph: dict[str, Any], runs: int = 1) -> dict[str, Any] | None:
    """Submit generation request to queue."""
    payload = {"batch": {"graph": graph, "runs": runs}, "prepend": False}
    result = api_request("/api/v1/queue/default/enqueue_batch", "POST", payload)
    return result if isinstance(result, dict) else None


def wait_for_completion(batch_id: str, item_id: str, timeout: int = 300) -> dict[str, Any] | None:
    """Poll queue until batch completes and return image info."""
    start = time.time()
    while time.time() - start < timeout:
        result = api_request(f"/api/v1/queue/default/b/{batch_id}/status")
        if not isinstance(result, dict):
            time.sleep(2)
            continue

        pending = result.get("pending", 0)
        in_progress = result.get("in_progress", 0)
        completed = result.get("completed", 0)
        failed = result.get("failed", 0)

        if failed > 0:
            print("Generation failed", file=sys.stderr)
            return {"status": "failed"}

        if completed > 0 and pending == 0 and in_progress == 0:
            # Get the image name from the queue item
            item_data = api_request(f"/api/v1/queue/default/i/{item_id}")
            if isinstance(item_data, dict):
                results = item_data.get("session", {}).get("results", {})
                for node_result in results.values():
                    if isinstance(node_result, dict) and "image" in node_result:
                        image_info = node_result["image"]
                        return {
                            "status": "completed",
                            "image_name": image_info.get("image_name"),
                        }
            return {"status": "completed"}

        print(".", end="", flush=True, file=sys.stderr)
        time.sleep(2)

    print("\nTimeout waiting for generation", file=sys.stderr)
    return {"status": "timeout"}


def generate_image(
    prompt: str,
    negative: str = "",
    model_key: str | None = None,
    width: int | None = None,
    height: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    scheduler: str | None = None,
    seed: int | None = None,
    output: str | None = None,
    wait: bool = True,
) -> dict[str, Any]:
    """Generate an image with the given parameters."""
    # Find a model if not specified
    models = list_models("main")
    if not models:
        return {"error": "No models installed"}

    selected_model: dict[str, Any] | None = None

    if model_key:
        # Find the specified model
        for m in models:
            if m["key"] == model_key:
                selected_model = m
                break
        if not selected_model:
            return {"error": f"Model {model_key} not found"}
    else:
        # Auto-select with strict priority: FLUX.2 Klein > Z-Image Turbo > FLUX.1 > SDXL
        # Search in priority order, not model list order
        for m in models:
            if "klein" in m.get("name", "").lower() or "flux2" in m.get("base", "").lower():
                selected_model = m
                break
        if not selected_model:
            for m in models:
                name = m.get("name", "").lower()
                if "z-image" in name or "zimage" in name:
                    selected_model = m
                    break
        if not selected_model:
            for m in models:
                if "flux" in m.get("base", "").lower():
                    selected_model = m
                    break
        if not selected_model:
            for m in models:
                if "sdxl" in m.get("base", "").lower():
                    selected_model = m
                    break
        if not selected_model:
            selected_model = models[0]

    model_type = detect_model_type(selected_model)
    defaults = get_defaults_for_model(model_type)

    # Apply defaults
    final_width: int = width or defaults["width"]
    final_height: int = height or defaults["height"]
    final_steps: int = steps or defaults["steps"]
    final_cfg: float = cfg if cfg is not None else defaults["cfg"]
    final_scheduler: str = scheduler or defaults["scheduler"]
    final_seed: int = seed if seed is not None else random.randint(0, 2**32 - 1)

    # Ensure dimensions divisible by 16 for FLUX models, 8 for others
    divisor = 16 if "flux" in model_type else 8
    final_width = (final_width // divisor) * divisor
    final_height = (final_height // divisor) * divisor

    # Build appropriate graph
    if model_type == "flux2_klein":
        graph = build_flux2_klein_graph(selected_model, prompt, final_width, final_height, final_steps, final_seed)
    elif model_type == "flux":
        graph = build_flux_graph(selected_model, prompt, final_width, final_height, final_steps, final_seed)
    else:
        graph = build_sdxl_graph(selected_model, prompt, negative, final_width, final_height, final_steps, final_cfg, final_scheduler, final_seed)

    # Submit to queue
    print(f"Generating with {selected_model.get('name')} ({model_type})...", file=sys.stderr)
    result = enqueue_generation(graph)
    if not result:
        return {"error": "Failed to enqueue generation"}

    batch_id = result.get("batch", {}).get("batch_id")
    item_ids = result.get("item_ids", [])
    item_id = item_ids[0] if item_ids else ""

    response: dict[str, Any] = {
        "batch_id": batch_id,
        "item_id": item_id,
        "model": selected_model.get("name"),
        "model_key": selected_model.get("key"),
        "model_type": model_type,
        "prompt": prompt,
        "seed": final_seed,
        "width": final_width,
        "height": final_height,
        "steps": final_steps,
        "cfg_scale": final_cfg,
        "scheduler": final_scheduler,
    }

    if wait and batch_id and item_id:
        status = wait_for_completion(batch_id, item_id)
        print(file=sys.stderr)  # Newline after progress dots
        response["status"] = status.get("status", "unknown") if status else "unknown"

        if status and status.get("image_name"):
            response["image_name"] = status["image_name"]

            # Download the image
            output_path = Path(output) if output else Path(f"invokeai-{final_seed}.png")
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading to {output_path}...", file=sys.stderr)
            if download_file(f"/api/v1/images/i/{status['image_name']}/full", output_path):
                response["output_file"] = str(output_path.absolute())
                print(f"Saved: {output_path}", file=sys.stderr)
            else:
                response["download_error"] = "Failed to download image"

    return response


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate images via InvokeAI API")
    parser.add_argument("--prompt", "-p", help="Generation prompt")
    parser.add_argument("--negative", "-n", default="", help="Negative prompt")
    parser.add_argument("--model", "-m", help="Model key (UUID)")
    parser.add_argument("--width", "-W", type=int, help="Image width")
    parser.add_argument("--height", "-H", type=int, help="Image height")
    parser.add_argument("--steps", "-s", type=int, help="Denoising steps")
    parser.add_argument("--cfg", "-c", type=float, help="CFG scale")
    parser.add_argument("--scheduler", help="Sampling scheduler")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    parser.add_argument("--list-models", action="store_true", help="List installed models")
    parser.add_argument("--model-info", help="Get model info by key")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    if not check_env():
        sys.exit(1)

    # List models
    if args.list_models:
        models = list_models("main")
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            for m in models:
                model_type = detect_model_type(m)
                print(f"{m['key']}: {m['name']} [{m.get('base', 'unknown')}] ({model_type})")
        sys.exit(0)

    # Model info
    if args.model_info:
        info = get_model_info(args.model_info)
        if info:
            print(json.dumps(info, indent=2))
            sys.exit(0)
        sys.exit(1)

    # Generate
    if not args.prompt:
        parser.error("--prompt is required for generation")

    result = generate_image(
        prompt=args.prompt,
        negative=args.negative,
        model_key=args.model,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg=args.cfg,
        scheduler=args.scheduler,
        seed=args.seed,
        output=args.output,
        wait=not args.no_wait,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"\nGeneration complete:")
        print(f"  Model: {result['model']} ({result['model_type']})")
        print(f"  Seed: {result['seed']}")
        print(f"  Size: {result['width']}x{result['height']}")
        print(f"  Steps: {result['steps']}, CFG: {result['cfg_scale']}")
        if result.get("output_file"):
            print(f"  File: {result['output_file']}")
        if result.get("status"):
            print(f"  Status: {result['status']}")


if __name__ == "__main__":
    main()
