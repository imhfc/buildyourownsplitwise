import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { Input } from "~/components/ui/input";

describe("Input component", () => {
  it("renders with label", () => {
    render(<Input label="Email" />);
    expect(screen.getByText("Email")).toBeTruthy();
  });

  it("renders with placeholder", () => {
    render(<Input placeholder="Enter email" />);
    expect(screen.getByPlaceholderText("Enter email")).toBeTruthy();
  });

  it("handles text change", () => {
    const onChangeText = jest.fn();
    render(<Input placeholder="Type here" onChangeText={onChangeText} />);
    fireEvent.changeText(screen.getByPlaceholderText("Type here"), "hello");
    expect(onChangeText).toHaveBeenCalledWith("hello");
  });

  it("displays error message", () => {
    render(<Input error="Required field" />);
    expect(screen.getByText("Required field")).toBeTruthy();
  });

  it("displays helper text when no error", () => {
    render(<Input helper="Optional field" />);
    expect(screen.getByText("Optional field")).toBeTruthy();
  });

  it("shows error instead of helper when both provided", () => {
    render(<Input error="Error!" helper="Helper" />);
    expect(screen.getByText("Error!")).toBeTruthy();
    expect(screen.queryByText("Helper")).toBeNull();
  });
});
