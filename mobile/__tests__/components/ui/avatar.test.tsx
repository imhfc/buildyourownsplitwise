import React from "react";
import { render, screen } from "@testing-library/react-native";
import { Avatar, AvatarStack } from "~/components/ui/avatar";

describe("Avatar component", () => {
  it("renders initials for CJK name", () => {
    render(<Avatar name="小明" />);
    expect(screen.getByText("小")).toBeTruthy();
  });

  it("renders initials for Latin name", () => {
    render(<Avatar name="Alice Wang" />);
    expect(screen.getByText("AW")).toBeTruthy();
  });

  it("renders initials for single-word name", () => {
    render(<Avatar name="bob" />);
    expect(screen.getByText("BO")).toBeTruthy();
  });

  it("renders ? for empty name", () => {
    render(<Avatar name="" />);
    expect(screen.getByText("?")).toBeTruthy();
  });
});

describe("AvatarStack component", () => {
  it("renders up to max avatars", () => {
    render(<AvatarStack names={["Alice", "Bob", "Carol"]} max={3} />);
    expect(screen.getByText("AL")).toBeTruthy();
    expect(screen.getByText("BO")).toBeTruthy();
    expect(screen.getByText("CA")).toBeTruthy();
  });

  it("shows +N indicator when more than max", () => {
    render(<AvatarStack names={["Alice", "Bob", "Carol", "Dave", "Eve"]} max={3} />);
    expect(screen.getByText("+2")).toBeTruthy();
  });

  it("does not show +N when exactly max", () => {
    render(<AvatarStack names={["Alice", "Bob"]} max={3} />);
    expect(screen.queryByText(/\+/)).toBeNull();
  });
});
