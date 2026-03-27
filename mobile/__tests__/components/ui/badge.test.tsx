import React from "react";
import { render, screen } from "@testing-library/react-native";
import { Badge } from "~/components/ui/badge";

describe("Badge component", () => {
  it("renders text content", () => {
    render(<Badge>TWD</Badge>);
    expect(screen.getByText("TWD")).toBeTruthy();
  });

  it("renders with secondary variant by default", () => {
    render(<Badge>Label</Badge>);
    expect(screen.getByText("Label")).toBeTruthy();
  });

  it("renders with different variants", () => {
    const { rerender } = render(<Badge variant="default">Default</Badge>);
    expect(screen.getByText("Default")).toBeTruthy();

    rerender(<Badge variant="destructive">Error</Badge>);
    expect(screen.getByText("Error")).toBeTruthy();

    rerender(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText("Outline")).toBeTruthy();
  });
});
