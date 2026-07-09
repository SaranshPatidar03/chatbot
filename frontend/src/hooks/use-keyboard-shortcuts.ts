import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!event.altKey) return;
      switch (event.key.toLowerCase()) {
        case "d":
          navigate("/app");
          break;
        case "c":
          navigate("/app/chat");
          break;
        case "k":
          navigate("/app/knowledge");
          break;
        case "s":
          navigate("/app/search");
          break;
        case ",":
          navigate("/app/settings");
          break;
        default:
          break;
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navigate]);
}
