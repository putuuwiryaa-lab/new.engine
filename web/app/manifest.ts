import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "NEW.ENGINE Research Console",
    short_name: "NEW.ENGINE",
    description: "Mobile-first research console for NEW.ENGINE market data and engine audits.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    orientation: "portrait-primary",
    background_color: "#070b12",
    theme_color: "#070b12",
    categories: ["utilities", "productivity"],
  };
}
