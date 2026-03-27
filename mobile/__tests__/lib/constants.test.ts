import { getAvatarColor, getInitials, AVATAR_COLORS } from "~/lib/constants";

describe("getAvatarColor", () => {
  it("returns correct color for index within range", () => {
    expect(getAvatarColor(0)).toBe("#2563EB");
    expect(getAvatarColor(1)).toBe("#7C3AED");
    expect(getAvatarColor(9)).toBe("#9333EA");
  });

  it("wraps around when index exceeds color count", () => {
    expect(getAvatarColor(10)).toBe(AVATAR_COLORS[0]);
    expect(getAvatarColor(11)).toBe(AVATAR_COLORS[1]);
    expect(getAvatarColor(25)).toBe(AVATAR_COLORS[5]);
  });
});

describe("getInitials", () => {
  it("returns first character for CJK names", () => {
    expect(getInitials("小明")).toBe("小");
    expect(getInitials("田中太郎")).toBe("田");
    expect(getInitials("あいう")).toBe("あ");
  });

  it("returns first two letters uppercase for single-word Latin names", () => {
    expect(getInitials("alice")).toBe("AL");
    expect(getInitials("Bob")).toBe("BO");
  });

  it("returns initials of first and last name for multi-word Latin names", () => {
    expect(getInitials("Alice Wang")).toBe("AW");
    expect(getInitials("john doe")).toBe("JD");
  });

  it("handles empty string", () => {
    expect(getInitials("")).toBe("?");
  });

  it("trims whitespace", () => {
    expect(getInitials("  Alice  Wang  ")).toBe("AW");
  });
});
