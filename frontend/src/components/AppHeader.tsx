import { JuggleLogo } from "./JuggleLogo";

export function AppHeader() {
  return (
    <header className="bg-[#0f2040] px-5 h-14 flex items-center shrink-0">
      {/* dir="ltr" so logo is to the right of the text in visual space */}
      <div className="flex items-center gap-2" dir="ltr">
        <span className="text-white font-bold text-lg tracking-wide">Juggle</span>
        <JuggleLogo size={26} />
      </div>
    </header>
  );
}
