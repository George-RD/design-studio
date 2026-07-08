import { registerRoot, Composition } from "remotion";
import { PromoVideo } from "./PromoVideo";
import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadManrope } from "@remotion/google-fonts/Manrope";
import { loadFont as loadSpaceMono } from "@remotion/google-fonts/SpaceMono";

// Load Google Fonts
loadFraunces();
loadManrope();
loadSpaceMono();

const RemotionRoot: React.FC = () => (
  <Composition
    id="DesignStudioPromo"
    component={PromoVideo}
    durationInFrames={60 * 23} // 23 seconds overview at 60fps
    fps={60}
    width={1920}
    height={1080}
  />
);
registerRoot(RemotionRoot);
