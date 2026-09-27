import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders the login screen when logged out", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "DemoBank" })).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/CUST1001/i)).toBeInTheDocument();
});
