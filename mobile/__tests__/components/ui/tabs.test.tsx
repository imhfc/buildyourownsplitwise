import React from "react";
import { render, screen, fireEvent } from "@testing-library/react-native";
import { SegmentedTabs } from "~/components/ui/tabs";

const TABS = [
  { value: "expenses", label: "消費紀錄" },
  { value: "settlements", label: "結算" },
];

describe("SegmentedTabs component", () => {
  it("renders all tab labels", () => {
    render(
      <SegmentedTabs tabs={TABS} value="expenses" onValueChange={() => {}} />
    );
    expect(screen.getByText("消費紀錄")).toBeTruthy();
    expect(screen.getByText("結算")).toBeTruthy();
  });

  it("calls onValueChange when a tab is pressed", () => {
    const onValueChange = jest.fn();
    render(
      <SegmentedTabs tabs={TABS} value="expenses" onValueChange={onValueChange} />
    );
    fireEvent.press(screen.getByText("結算"));
    expect(onValueChange).toHaveBeenCalledWith("settlements");
  });

  it("calls onValueChange with correct value for each tab", () => {
    const onValueChange = jest.fn();
    render(
      <SegmentedTabs tabs={TABS} value="settlements" onValueChange={onValueChange} />
    );
    fireEvent.press(screen.getByText("消費紀錄"));
    expect(onValueChange).toHaveBeenCalledWith("expenses");
  });
});
