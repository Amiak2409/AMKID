import { useEffect, useRef, useState } from "react";

export function useTypewriter(delay = 170) {
  const [text, setText] = useState("");
  const intervalRef = useRef<number | null>(null);

  const clear = () => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const start = (fullText: string) => {
    clear();

    const words = fullText.split(" ").filter(Boolean);
    let index = 0;
    let currentText = "";

    setText("");

    intervalRef.current = window.setInterval(() => {
      if (index >= words.length) {
        clear();
        return;
      }

      currentText = index === 0 ? words[0] : `${currentText} ${words[index]}`;
      index += 1;

      setText(currentText);
    }, delay);
  };

  useEffect(() => {
    return () => {
      clear();
    };
  }, []);

  return { text, start, stop: clear };
}
