import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarkdownContent } from "@/components/chat/markdown-content";

describe("MarkdownContent", () => {
  it("renders inline code and bold text", () => {
    render(<MarkdownContent content="Use **bold** and `code` here." />);
    expect(screen.getByText("bold")).toBeInTheDocument();
    expect(screen.getByText("code")).toBeInTheDocument();
  });

  it("renders fenced code blocks", () => {
    render(<MarkdownContent content={"```python\nprint('hi')\n```"} />);
    expect(screen.getByText("print('hi')")).toBeInTheDocument();
  });

  it("renders plain text for user messages", () => {
    render(<MarkdownContent content="Hello **world**" plain />);
    expect(screen.getByText("Hello **world**")).toBeInTheDocument();
  });
});
