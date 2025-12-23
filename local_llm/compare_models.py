"""
Compare multiple LLM models on the same task
Runs Google search demo with different models and generates comparison report
"""
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Add to path
local_llm_dir = os.path.dirname(__file__)
playground_dir = os.path.dirname(local_llm_dir)
sys.path.insert(0, local_llm_dir)
sys.path.insert(0, playground_dir)

from demos.google_search import run_google_search_demo


# Model configurations to compare
MODEL_CONFIGS = [
    {
        "name": "Qwen 2.5 3B",
        "config": {
            "type": "local",
            "model_name": "Qwen/Qwen2.5-3B-Instruct",
            "device": "auto",
            "load_in_4bit": False
        }
    },
    {
        "name": "Qwen 2.5 3B (4-bit)",
        "config": {
            "type": "local",
            "model_name": "Qwen/Qwen2.5-3B-Instruct",
            "device": "auto",
            "load_in_4bit": True
        }
    },
    {
        "name": "Gemma 2 2B",
        "config": {
            "type": "local",
            "model_name": "google/gemma-2-2b-it",
            "device": "auto",
            "load_in_4bit": False
        }
    },
    {
        "name": "GPT-4 Turbo (baseline)",
        "config": {
            "type": "cloud",
            "model": "gpt-4-turbo-preview"
        }
    }
]


def run_comparison(
    models: List[Dict[str, Any]],
    search_query: str = "visiting japan",
    output_dir: str = None
) -> Dict[str, Any]:
    """
    Run comparison across multiple models

    Args:
        models: List of model configurations
        search_query: Search query to use
        output_dir: Directory to save results

    Returns:
        Comparison results dictionary
    """
    if output_dir is None:
        output_dir = os.path.join(local_llm_dir, "comparisons")

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_results = {
        "timestamp": timestamp,
        "search_query": search_query,
        "models": []
    }

    print(f"\n{'='*80}")
    print(f" "*25 + "MODEL COMPARISON")
    print(f"{'='*80}")
    print(f"Search query: '{search_query}'")
    print(f"Models to compare: {len(models)}")
    print(f"{'='*80}\n")

    for i, model_info in enumerate(models, 1):
        model_name = model_info["name"]
        model_config = model_info["config"]

        print(f"\n{'#'*80}")
        print(f"Model {i}/{len(models)}: {model_name}")
        print(f"{'#'*80}\n")

        try:
            # Run demo
            results = run_google_search_demo(
                llm_config=model_config,
                search_query=search_query
            )

            # Extract key metrics
            model_results = {
                "name": model_name,
                "config": model_config,
                "success": results.get("success", False),
                "duration_seconds": results.get("duration_seconds", 0),
                "total_tokens": results.get("token_summary", {}).get("total_tokens", 0),
                "prompt_tokens": results.get("token_summary", {}).get("total_prompt_tokens", 0),
                "completion_tokens": results.get("token_summary", {}).get("total_completion_tokens", 0),
                "final_url": results.get("final_url", "N/A"),
                "scenes": results.get("scenes", []),
                "error": results.get("error")
            }

            comparison_results["models"].append(model_results)

            print(f"\n✅ {model_name} completed")
            print(f"   Success: {model_results['success']}")
            print(f"   Tokens: {model_results['total_tokens']}")
            print(f"   Duration: {model_results['duration_seconds']:.1f}s")

        except Exception as e:
            print(f"\n❌ {model_name} failed: {e}")
            import traceback
            traceback.print_exc()

            comparison_results["models"].append({
                "name": model_name,
                "config": model_config,
                "success": False,
                "error": str(e)
            })

    # Save comparison results
    output_file = os.path.join(output_dir, f"comparison_{timestamp}.json")
    with open(output_file, 'w') as f:
        json.dump(comparison_results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Comparison results saved: {output_file}")
    print(f"{'='*80}\n")

    # Generate summary
    print_comparison_summary(comparison_results)

    # Generate markdown report
    report_file = os.path.join(output_dir, f"comparison_{timestamp}.md")
    generate_markdown_report(comparison_results, report_file)
    print(f"\n📄 Markdown report: {report_file}\n")

    return comparison_results


def print_comparison_summary(results: Dict[str, Any]):
    """Print comparison summary table"""
    print(f"\n{'='*80}")
    print(f" "*28 + "COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    # Table header
    print(f"{'Model':<30} {'Success':<10} {'Tokens':<12} {'Duration':<12} {'URL Match':<10}")
    print(f"{'-'*30} {'-'*10} {'-'*12} {'-'*12} {'-'*10}")

    for model in results["models"]:
        name = model["name"][:29]
        success = "✅" if model.get("success") else "❌"
        tokens = model.get("total_tokens", 0)
        duration = model.get("duration_seconds", 0)
        has_url = "✅" if model.get("final_url") and model.get("final_url") != "N/A" else "❌"

        print(f"{name:<30} {success:<10} {tokens:<12} {duration:<12.1f}s {has_url:<10}")

    print(f"\n{'='*80}\n")


def generate_markdown_report(results: Dict[str, Any], output_file: str):
    """Generate markdown comparison report"""

    successful_models = [m for m in results["models"] if m.get("success")]

    if not successful_models:
        print("⚠️ No successful models to compare")
        return

    # Calculate winner metrics
    min_tokens = min(m["total_tokens"] for m in successful_models)
    min_duration = min(m["duration_seconds"] for m in successful_models)

    report = f"""# Local LLM Comparison Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Task**: Google Search - "{results['search_query']}"
**Models Tested**: {len(results['models'])}

---

## Results Summary

| Model | Success | Total Tokens | Duration (s) | Prompt Tokens | Completion Tokens |
|-------|---------|--------------|--------------|---------------|-------------------|
"""

    for model in results["models"]:
        name = model["name"]
        success = "✅" if model.get("success") else "❌"
        tokens = model.get("total_tokens", 0)
        duration = model.get("duration_seconds", 0)
        prompt_tokens = model.get("prompt_tokens", 0)
        completion_tokens = model.get("completion_tokens", 0)

        # Highlight winners
        token_marker = " 🏆" if model.get("success") and tokens == min_tokens else ""
        duration_marker = " ⚡" if model.get("success") and duration == min_duration else ""

        report += f"| {name} | {success} | {tokens}{token_marker} | {duration:.1f}{duration_marker} | {prompt_tokens} | {completion_tokens} |\n"

    report += f"""
---

## Analysis

### Token Efficiency
"""

    if len(successful_models) > 1:
        sorted_by_tokens = sorted(successful_models, key=lambda x: x["total_tokens"])
        best_model = sorted_by_tokens[0]
        worst_model = sorted_by_tokens[-1]

        report += f"""
- **Most efficient**: {best_model['name']} ({best_model['total_tokens']} tokens)
- **Least efficient**: {worst_model['name']} ({worst_model['total_tokens']} tokens)
- **Difference**: {worst_model['total_tokens'] - best_model['total_tokens']} tokens ({((worst_model['total_tokens'] / best_model['total_tokens']) - 1) * 100:.1f}% more)
"""

    report += f"""
### Speed
"""

    if len(successful_models) > 1:
        sorted_by_duration = sorted(successful_models, key=lambda x: x["duration_seconds"])
        fastest_model = sorted_by_duration[0]
        slowest_model = sorted_by_duration[-1]

        report += f"""
- **Fastest**: {fastest_model['name']} ({fastest_model['duration_seconds']:.1f}s)
- **Slowest**: {slowest_model['name']} ({slowest_model['duration_seconds']:.1f}s)
- **Difference**: {slowest_model['duration_seconds'] - fastest_model['duration_seconds']:.1f}s ({((slowest_model['duration_seconds'] / fastest_model['duration_seconds']) - 1) * 100:.1f}% slower)
"""

    report += f"""
---

## Per-Scene Breakdown

"""

    for model in results["models"]:
        if not model.get("success"):
            continue

        report += f"""### {model['name']}

"""
        for scene in model.get("scenes", []):
            scene_name = scene.get("name", "Unknown")
            tokens = scene.get("tokens", 0)
            reasoning = scene.get("reasoning", "N/A")

            report += f"""**{scene_name}**
- Tokens: {tokens}
- Reasoning: {reasoning}

"""

    report += f"""
---

## Recommendations

"""

    if successful_models:
        # Find best overall model
        # Score: lower tokens + faster duration = better
        for model in successful_models:
            model["score"] = (model["total_tokens"] / min_tokens) + (model["duration_seconds"] / min_duration)

        best_overall = min(successful_models, key=lambda x: x["score"])

        report += f"""
### Best Overall: {best_overall['name']}

This model offers the best balance of token efficiency and speed.

- **Total Tokens**: {best_overall['total_tokens']}
- **Duration**: {best_overall['duration_seconds']:.1f}s
- **Prompt Tokens**: {best_overall['prompt_tokens']}
- **Completion Tokens**: {best_overall['completion_tokens']}

"""

    # Add failed models if any
    failed_models = [m for m in results["models"] if not m.get("success")]
    if failed_models:
        report += f"""
### Failed Models

The following models did not complete the task successfully:

"""
        for model in failed_models:
            error = model.get("error", "Unknown error")
            report += f"- **{model['name']}**: {error}\n"

    # Write report
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"✅ Markdown report generated: {output_file}")


def main():
    """Run comparison with predefined models"""

    # You can customize which models to compare
    # Comment out models you don't want to test
    models_to_test = [
        MODEL_CONFIGS[0],  # Qwen 2.5 3B
        # MODEL_CONFIGS[1],  # Qwen 2.5 3B (4-bit) - uncomment if you want to test quantized version
        # MODEL_CONFIGS[2],  # Gemma 2 2B - uncomment if you have this model downloaded
        # MODEL_CONFIGS[3],  # GPT-4 Turbo - uncomment if you have OpenAI API key
    ]

    results = run_comparison(models_to_test)

    print("\n🎉 Comparison complete!")
    print(f"   Models tested: {len(results['models'])}")
    successful = sum(1 for m in results['models'] if m.get('success'))
    print(f"   Successful: {successful}/{len(results['models'])}")


if __name__ == "__main__":
    main()
