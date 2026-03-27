import React from "react";
import { render, screen } from "@testing-library/react-native";
import { Text, H1, H2, H3, Muted } from "~/components/ui/text";

describe("Text components", () => {
  it("renders Text with children", () => {
    render(<Text>Hello World</Text>);
    expect(screen.getByText("Hello World")).toBeTruthy();
  });

  it("renders H1 with children", () => {
    render(<H1>Title</H1>);
    expect(screen.getByText("Title")).toBeTruthy();
  });

  it("renders H2 with children", () => {
    render(<H2>Subtitle</H2>);
    expect(screen.getByText("Subtitle")).toBeTruthy();
  });

  it("renders H3 with children", () => {
    render(<H3>Section</H3>);
    expect(screen.getByText("Section")).toBeTruthy();
  });

  it("renders Muted with children", () => {
    render(<Muted>Helper text</Muted>);
    expect(screen.getByText("Helper text")).toBeTruthy();
  });
});
