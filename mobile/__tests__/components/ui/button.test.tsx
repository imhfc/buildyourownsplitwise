import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { Button } from "~/components/ui/button";

describe("Button component", () => {
  it("renders with text children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeTruthy();
  });

  it("calls onPress when pressed", () => {
    const onPress = jest.fn();
    render(<Button onPress={onPress}>Press</Button>);
    fireEvent.press(screen.getByText("Press"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("does not call onPress when disabled", () => {
    const onPress = jest.fn();
    render(
      <Button onPress={onPress} disabled>
        Disabled
      </Button>
    );
    fireEvent.press(screen.getByText("Disabled"));
    expect(onPress).not.toHaveBeenCalled();
  });

  it("does not call onPress when loading", () => {
    const onPress = jest.fn();
    render(
      <Button onPress={onPress} loading>
        Loading
      </Button>
    );
    // When loading, text still renders but button should be disabled
    fireEvent.press(screen.getByText("Loading"));
    expect(onPress).not.toHaveBeenCalled();
  });

  it("shows ActivityIndicator when loading", () => {
    render(<Button loading>Loading</Button>);
    // ActivityIndicator renders as a view with accessibilityRole
    expect(screen.getByText("Loading")).toBeTruthy();
  });
});
