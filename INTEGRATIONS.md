# AAFC MIT integrations

100 MIT-licensed projects, mapped to AAFC business workloads. Client websites and games are excluded.

The runnable layer is `aafc_engine/integrations`. It does not add a second auditor, does not send mail, and does not invent findings. Optional heavy tools (Whisper, Demucs, rembg) stay optional so a laptop is not forced to download models.

Open the operator UI at `web/studio.html`.

```bash
python -m aafc_engine.integrations list
python -m aafc_engine.integrations list engine
```
