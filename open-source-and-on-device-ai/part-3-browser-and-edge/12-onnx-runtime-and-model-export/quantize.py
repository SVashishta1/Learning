# Step 3: shrink the ONNX model with dynamic quantization (32-bit weights -> 8-bit weights).
import sys
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic

SOURCE = Path("exported/model.onnx")
TARGET = Path("exported/model-int8.onnx")
if not SOURCE.exists():
    sys.exit(f"Can't find {SOURCE}. Run 'python export_to_onnx.py' first.")

# The exporter stores "shape notes" (value_info) for every in-between result. The quantizer
# recalculates them itself and can disagree with the stored ones, so we hand it a copy without them.
model = onnx.load(SOURCE)
model.graph.ClearField("value_info")
clean = SOURCE.with_name("model-clean.onnx")
onnx.save(model, clean)

quantize_dynamic(clean, TARGET, weight_type=QuantType.QInt8)    # weights become int8, activations stay float
clean.unlink()                                                   # remove the temporary copy

before, after = SOURCE.stat().st_size / 1e6, TARGET.stat().st_size / 1e6
print(f"✅ {SOURCE.name}: {before:.1f} MB  ->  {TARGET.name}: {after:.1f} MB  ({after / before:.0%} of the size)")
