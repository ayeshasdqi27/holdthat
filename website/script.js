/* ==========================================================================
   hold that — Redesigned Page 1 Script (GSAP Interactivity)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  const cardToday = document.getElementById('cardToday');
  const cardYesterday = document.getElementById('cardYesterday');
  const dateToday = document.getElementById('dateToday');
  const dateYesterday = document.getElementById('dateYesterday');

  // --- 1. Interactive SVG Grid with Dynamic GSAP Mouse Glow ---
  const gridContainer = document.getElementById('gridContainer');
  const gridSvg = document.getElementById('gridSvg');

  // Track coordinates relative to SVG viewBox (1517 x 992)
  function handleMouseMove(e) {
    const rect = gridSvg.getBoundingClientRect();
    
    // Map mouse position to viewBox coordinate system
    const svgX = (e.clientX - rect.left) * (1517 / rect.width);
    const svgY = (e.clientY - rect.top) * (992 / rect.height);

    // Smoothly follow mouse with GSAP
    gsap.to('#gridGlowGradient', {
      attr: { cx: svgX, cy: svgY },
      duration: 0.25,
      ease: 'power1.out'
    });
  }

  let isGlowActive = false;

  // Activate glow stops on enter
  function handleMouseEnter() {
    if (isGlowActive) return;
    isGlowActive = true;
    gsap.to('#glowStop0', {
      stopColor: '#FFF2D5',
      duration: 0.15
    });
  }

  // Fade back to normal on leave
  function handleMouseLeave() {
    isGlowActive = false;
    gsap.to('#glowStop0', {
      stopColor: '#FFF9EC',
      duration: 1.2,
      ease: 'power2.out'
    });
    // Move glow off screen
    gsap.to('#gridGlowGradient', {
      attr: { cx: -500, cy: -500 },
      duration: 1.2,
      ease: 'power2.out'
    });
  }

  // Bind window-wide mouse move and leave events
  document.addEventListener('mousemove', (e) => {
    handleMouseEnter();
    handleMouseMove(e);
  });
  document.addEventListener('mouseleave', handleMouseLeave);

  // --- 2. Dynamic Dates Formatting (lowercase, month and day) ---
  function getFormattedDate(offsetDays = 0) {
    const d = new Date();
    d.setDate(d.getDate() - offsetDays);
    const month = d.toLocaleString('default', { month: 'long' }).toLowerCase();
    const day = d.getDate();
    return `${month} ${day}`;
  }

  if (dateToday && dateYesterday) {
    dateToday.textContent = getFormattedDate(0);
    dateYesterday.textContent = getFormattedDate(1);
  }

  // --- 3. Hero Images Loop Transition ---
  const heroImg1 = document.getElementById('heroImg1');
  const heroImg2 = document.getElementById('heroImg2');
  if (heroImg1 && heroImg2) {
    let currentHero = 1;
    setInterval(() => {
      if (currentHero === 1) {
        heroImg1.classList.remove('active');
        heroImg2.classList.add('active');
        currentHero = 2;
      } else {
        heroImg2.classList.remove('active');
        heroImg1.classList.add('active');
        currentHero = 1;
      }
    }, 2000);
  }

  // --- 3.1 3D Card Shuffling depth swap (GSAP Animation) [Fallback] ---
  if (cardToday && cardYesterday) {
    let activeFrontCard = 'yesterday'; // In Figma layout, Yesterday sits upright in front
    let isShuffling = false;

    function shuffleCards(targetCard) {
      if (isShuffling || activeFrontCard === targetCard) return;
      isShuffling = true;

      const isTodayTarget = targetCard === 'today';
      const front = isTodayTarget ? cardYesterday : cardToday;
      const back = isTodayTarget ? cardToday : cardYesterday;

      // Creative GSAP timeline mimicking a card shuffle deck swap
      const tl = gsap.timeline({
        onComplete: () => {
          activeFrontCard = targetCard;
          isShuffling = false;
        }
      });

      // Step 1: Slide them outward slightly to separate their bounds
      tl.to(front, {
        x: isTodayTarget ? -50 : 50,
        y: isTodayTarget ? 10 : -10,
        rotate: isTodayTarget ? -8 : 8,
        scale: 0.98,
        duration: 0.25,
        ease: 'power2.out'
      });

      tl.to(back, {
        x: isTodayTarget ? 50 : -50,
        y: isTodayTarget ? -10 : 10,
        rotate: isTodayTarget ? 8 : -8,
        scale: 1.02,
        duration: 0.25,
        ease: 'power2.out'
      }, 0);

      // Step 2: Swap z-index halfway through the animation
      tl.add(() => {
        if (isTodayTarget) {
          cardToday.style.zIndex = '20';
          cardYesterday.style.zIndex = '10';
        } else {
          cardYesterday.style.zIndex = '20';
          cardToday.style.zIndex = '10';
        }
      });

      // Step 3: Slide them back together with target orientations
      tl.to(cardToday, {
        x: isTodayTarget ? 0 : 20,
        y: isTodayTarget ? 0 : -20,
        rotate: isTodayTarget ? 0 : 15,
        scale: 1,
        duration: 0.35,
        ease: 'back.out(1.2)'
      });

      tl.to(cardYesterday, {
        x: isTodayTarget ? -20 : 0,
        y: isTodayTarget ? 20 : 0,
        rotate: isTodayTarget ? -12 : 0,
        scale: 1,
        duration: 0.35,
        ease: 'back.out(1.2)'
      }, '-=0.35');
    }

    // Clicking cards triggers the 3D shuffle swap
    cardToday.addEventListener('click', () => shuffleCards('today'));
    cardYesterday.addEventListener('click', () => shuffleCards('yesterday'));
  }

  // --- 3.5 Dynamic Slot Machine Letter Reels Generation ---
  const rollerContainer = document.getElementById('letterRollerContainer');
  if (rollerContainer) {
    const words = [
      "second brain.",
      "productivity system.",
      "knowledge base."
    ];
    const maxLength = Math.max(...words.map(w => w.length));
    
    rollerContainer.innerHTML = ''; // Clear fallback contents
    
    for (let i = 0; i < maxLength; i++) {
      const reel = document.createElement('div');
      reel.className = 'letter-reel';
      
      const reelList = document.createElement('div');
      reelList.className = 'letter-reel-list';
      
      for (let j = 0; j < words.length; j++) {
        const item = document.createElement('div');
        item.className = 'letter-item';
        // Get character at index i, fallback to non-breaking space
        const char = words[j][i] || '\u00A0';
        item.textContent = char;
        reelList.appendChild(item);
      }
      
      reel.appendChild(reelList);
      rollerContainer.appendChild(reel);
    }
  }

  // --- 4. Page 2 to Page 3 ScrollTrigger Presentation Animation ---
  const mockupToday = document.getElementById('mockupToday');
  const mockupYesterday = document.getElementById('mockupYesterday');

  // Register GSAP ScrollTrigger
  gsap.registerPlugin(ScrollTrigger);

  const presentationTl = gsap.timeline({
    scrollTrigger: {
      trigger: "#scrollPresentation",
      start: "top top",
      end: "+=600%",
      pin: true,
      scrub: 2
    }
  });

  // Timeline Step 1: Slide & fade out Page 2 text slide (starts at 0.2 after buffer)
  presentationTl.to("#slidePage2", {
    opacity: 0,
    y: -30,
    duration: 0.4
  }, 0.2);

  // Timeline Step 2: Slide & fade in Page 3 text slide
  presentationTl.to("#slidePage3", {
    opacity: 1,
    y: 0,
    duration: 0.4
  }, 0.5);

  // Timeline Step 3: Blend presentation section background from white to dark charcoal
  presentationTl.to("#scrollPresentation", {
    backgroundColor: "#1C1C1C",
    duration: 0.6
  }, 0.2);

  // Timeline Step 4: Dim the global background grid opacity to represent night mode
  presentationTl.to("#gridContainer", {
    opacity: 0.15,
    duration: 0.6
  }, 0.2);

  // Timeline Step 5: Crossfade today → yesterday mockup
  // today fades out as yesterday fades in
  presentationTl.to("#mockupToday", {
    opacity: 0,
    duration: 0.35
  }, 0.5);

  presentationTl.to("#mockupYesterday", {
    opacity: 1,
    duration: 0.35
  }, 0.6);

  // Timeline Step 6: Transition header text to white as the background turns dark
  presentationTl.to(".header-title, .nav-link", {
    color: "#FFFFFF",
    duration: 0.4
  }, 0.5);



  // --- 5. Page 4 Pinned Clutter Deck Animations ---
  
  const clutterTl = gsap.timeline({
    scrollTrigger: {
      trigger: "#clutterSection",
      start: "top top",
      end: "+=700%",
      pin: true,
      scrub: 1
    }
  });

  // A. Background color transitions from Page 3 charcoal (#1C1C1C) to transparent (revealing white grid)
  clutterTl.to("#clutterSection", 
    { backgroundColor: "rgba(253, 255, 255, 0)", duration: 1.0, ease: "power1.inOut" },
    0
  );

  // B. Restore global grid opacity to full 1.0
  clutterTl.to("#gridContainer",
    { opacity: 1, duration: 1.0, ease: "power1.inOut" },
    0
  );

  // B2. Transition header text to black as background turns light
  clutterTl.to(".header-title, .nav-link", {
    color: "#000000",
    duration: 1.0,
    ease: "power1.inOut"
  }, 0);

  // C. Pinned sequence: card deck swap animations
  
  // Card 1: Slide in from bottom
  clutterTl.fromTo("#clutterCard1",
    { y: 800, opacity: 0, rotation: 10 },
    { y: 0, opacity: 1, rotation: 0, duration: 0.8, ease: "power2.out" },
    1.0
  );

  // Card 1 slides out (top-left) & Card 2 slides in (bottom-right)
  clutterTl.to("#clutterCard1", {
    x: -600,
    y: -200,
    rotation: -25,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 2.0);

  clutterTl.fromTo("#clutterCard2",
    { x: 600, y: 400, rotation: 35, opacity: 0 },
    { x: 0, y: 0, rotation: 7.3, opacity: 1, duration: 0.8, ease: "power2.out" },
    2.2
  );

  // Card 2 slides out (top-right) & Card 3 slides in (bottom-left)
  clutterTl.to("#clutterCard2", {
    x: 600,
    y: -200,
    rotation: 25,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 3.2);

  clutterTl.fromTo("#clutterCard3",
    { x: -600, y: 400, rotation: -30, opacity: 0 },
    { x: 0, y: 0, rotation: -5, opacity: 1, duration: 0.8, ease: "power2.out" },
    3.4
  );

  // Card 3 slides out (left) & Card 4 slides in (right)
  clutterTl.to("#clutterCard3", {
    x: -700,
    rotation: -15,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 4.4);

  clutterTl.fromTo("#clutterCard4",
    { x: 700, y: 0, rotation: 25, opacity: 0 },
    { x: 0, y: 0, rotation: -7.6, opacity: 1, duration: 0.8, ease: "power2.out" },
    4.6
  );

  // Card 4 slides out (bottom-left) & Card 5 slides in (top-right)
  clutterTl.to("#clutterCard4", {
    x: -400,
    y: 500,
    rotation: -35,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 5.6);

  clutterTl.fromTo("#clutterCard5",
    { x: 500, y: -400, rotation: -15, opacity: 0 },
    { x: 0, y: 0, rotation: 3, opacity: 1, duration: 0.8, ease: "power2.out" },
    5.8
  );

  // Card 5 slides out (top) & Card 6 slides in (bottom)
  clutterTl.to("#clutterCard5", {
    y: -600,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 6.8);

  clutterTl.fromTo("#clutterCard6",
    { y: 600, rotation: -15, opacity: 0 },
    { y: 0, rotation: 4.32, opacity: 1, duration: 0.8, ease: "power2.out" },
    7.0
  );

  // Card 6 slides out (bottom) & Summary fades in (center)
  clutterTl.to("#clutterCard6", {
    y: 700,
    rotation: 15,
    opacity: 0,
    duration: 0.8,
    ease: "power2.in"
  }, 8.0);

  clutterTl.fromTo("#clutterSummary",
    { y: 60, opacity: 0 },
    { y: 0, opacity: 1, duration: 0.8, ease: "power2.out" },
    8.2
  );

  // Buffer space at the end to keep the final summary visible
  clutterTl.to({}, { duration: 0.8 });

  // --- 5.5 Page 5 Pinned Folder Note Fall Animation ---
  const page5Tl = gsap.timeline({
    scrollTrigger: {
      trigger: "#page5",
      start: "top top",
      end: "+=200%",
      pin: true,
      scrub: 1
    }
  });

  // Add buffer at start so nothing happens immediately on entering the page
  page5Tl.to({}, { duration: 0.8 });

  // Step 1: Clip opens up, tilts, and slides off left
  page5Tl.to("#page5Clip", {
    rotation: 15,       // subtle rotation open
    x: -8,              // subtle slide left
    y: 4,               // subtle fall
    duration: 0.8,
    ease: "power2.inOut"
  }, 0.8);

  // Step 2: Note falls down (slipping out, rotating clockwise, fading out)
  page5Tl.to("#page5Note", {
    y: 850,             // fall out of screen bounds
    x: -80,             // slide left as it slips
    rotation: 25,       // tilt clockwise as it slips
    opacity: 0,         // fade out
    duration: 1.2,
    ease: "power2.in"   // speed up as it falls (gravity)
  }, 1.2); // starts shortly after clip opens
  // --- 6. Pages 6-8 Pinned Slot Machine Roller ---
  const slotTl = gsap.timeline({
    scrollTrigger: {
      trigger: "#slotMachineSection",
      start: "top top",
      end: "+=250%",
      pin: true,
      scrub: 1
    }
  });

  // Set initial states for illustrations
  gsap.set("#illPage6", { opacity: 1, y: 0 });
  gsap.set("#illPage7", { opacity: 0, y: 50 });
  gsap.set("#illPage8", { opacity: 0, y: 50 });
  gsap.set("#orangeDotPage8", { opacity: 0, y: 50 });

  // Get all letter reel lists for animation
  const letterReels = document.querySelectorAll('.letter-reel-list');

  // Page 6 -> Page 7
  slotTl.to("#illPage6", {
    opacity: 0,
    y: -50,
    duration: 0.8,
    ease: "power2.inOut"
  }, 0);

  slotTl.to(letterReels, {
    yPercent: -33.33,
    duration: 0.8,
    stagger: 0.025,
    ease: "back.inOut(1.2)" // Snappy split-flap style bounce
  }, 0);

  slotTl.to("#illPage7", {
    opacity: 1,
    y: 0,
    duration: 0.8,
    ease: "power2.inOut"
  }, 0.2);

  // Page 7 -> Page 8
  slotTl.to("#illPage7", {
    opacity: 0,
    y: -50,
    duration: 0.8,
    ease: "power2.inOut"
  }, 1.2);

  slotTl.to(letterReels, {
    yPercent: -66.66,
    duration: 0.8,
    stagger: 0.025,
    ease: "back.inOut(1.2)"
  }, 1.2);

  slotTl.to(["#illPage8", "#orangeDotPage8"], {
    opacity: 1,
    y: 0,
    duration: 0.8,
    ease: "power2.inOut"
  }, 1.4);

  // Hold Page 8
  slotTl.to({}, { duration: 0.6 });


  // --- 7. Pages 9-11 Pinned Hand-Washing Smooth Scroll Animation ---
  const washTl = gsap.timeline({
    scrollTrigger: {
      trigger: "#handWashSection",
      start: "top top",
      end: "+=250%",
      pin: true,
      scrub: 1
    }
  });

  // Set initial states
  gsap.set("#handFrameDraw", { opacity: 1 });
  gsap.set("#handFrameWater", { opacity: 0 });
  gsap.set("#handFrameClean", { opacity: 0 });
  gsap.set("#handDynamicLine", { opacity: 0 });
  gsap.set("#handFadeSpan", { opacity: 0 });
  gsap.set("#handDownloadGroup", { opacity: 0 });

  // Phase 1 (0.0 to 1.2): Draw hand fades to Water hand, "except your" fades in
  washTl.to("#handFrameDraw", {
    opacity: 0,
    duration: 1.2,
    ease: "power1.inOut"
  }, 0);

  washTl.to("#handFrameWater", {
    opacity: 1,
    duration: 1.2,
    ease: "power1.inOut"
  }, 0);

  washTl.to("#handDynamicLine", {
    opacity: 1,
    duration: 1.0,
    ease: "power1.inOut"
  }, 0.2);

  // Phase 2 (1.5 to 2.7): Water hand fades to Clean hand, "hand gets washed." fades in
  washTl.to("#handFrameWater", {
    opacity: 0,
    duration: 1.2,
    ease: "power1.inOut"
  }, 1.5);

  washTl.to("#handFrameClean", {
    opacity: 1,
    duration: 1.2,
    ease: "power1.inOut"
  }, 1.5);

  washTl.to("#handFadeSpan", {
    opacity: 1,
    duration: 1.0,
    ease: "power1.inOut"
  }, 1.7);

  // Phase 3 (2.0 to 3.0): Download group fades in at the end
  washTl.to("#handDownloadGroup", {
    opacity: 1,
    duration: 1.0,
    ease: "power1.inOut"
  }, 2.0);

  // Hold state at the end
  washTl.to({}, { duration: 0.5 });


  // --- 8. IDGI Mockup Images Loop Transition ---
  const idgiImg1 = document.getElementById('idgiImg1');
  const idgiImg2 = document.getElementById('idgiImg2');
  if (idgiImg1 && idgiImg2) {
    let currentIdgi = 1;
    setInterval(() => {
      if (currentIdgi === 1) {
        idgiImg1.classList.remove('active');
        idgiImg2.classList.add('active');
        currentIdgi = 2;
      } else {
        idgiImg2.classList.remove('active');
        idgiImg1.classList.add('active');
        currentIdgi = 1;
      }
    }, 2000);
  }


  // --- 8.5 IDGI Section Sticky Header Theme Toggle ---
  ScrollTrigger.create({
    trigger: "#idgiSection",
    start: "top 64px",
    end: "bottom top",
    onEnter: () => gsap.to(".header-title, .nav-link", { color: "#FFFFFF", duration: 0.3, ease: "power1.out" }),
    onLeaveBack: () => gsap.to(".header-title, .nav-link", { color: "#000000", duration: 0.3, ease: "power1.out" })
  });


  // --- 8.8 Navigation Smooth Scroll Hijack for GSAP Pins ---
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      
      let scrollTarget = 0;
      if (targetId === '#scrollPresentation') {
        scrollTarget = presentationTl.scrollTrigger.start;
      } else if (targetId === '#clutterSection') {
        const start = clutterTl.scrollTrigger.start;
        const end = clutterTl.scrollTrigger.end;
        scrollTarget = start + 0.13 * (end - start);
      } else if (targetId === '#slotMachineSection') {
        scrollTarget = slotTl.scrollTrigger.start;
      } else {
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          scrollTarget = targetEl.offsetTop;
        }
      }

      const obj = { y: window.scrollY };
      gsap.to(obj, {
        y: scrollTarget,
        duration: 1.2,
        ease: 'power2.out',
        onUpdate: () => window.scrollTo(0, obj.y)
      });
    });
  });


  // --- 9. Responsive Scale Adjustments for 1440x1024 Containers ---
  function scaleContainers() {
    const containers = document.querySelectorAll('.page5-container, .slot-machine-container, .hand-wash-container, .idgi-container');
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    if (windowWidth < 992) {
      // Mobile layout matches CSS media queries
      containers.forEach(el => {
        el.style.transform = '';
        el.style.transformOrigin = '';
      });
      return;
    }

    // Centered scaling to fit window aspect bounds of 1440x1024
    const scaleX = windowWidth / 1440;
    const scaleY = windowHeight / 1024;
    const scale = Math.min(scaleX, scaleY, 1); // Cap scale at 1 to prevent visual pixelation

    containers.forEach(el => {
      el.style.transform = `scale(${scale})`;
      el.style.transformOrigin = 'center center';
    });
  }

  window.addEventListener('resize', scaleContainers);
  scaleContainers(); // Initialize scale factor on load
  
  // Refresh ScrollTrigger to recalculate pins after scaling adjustments
  ScrollTrigger.addEventListener('refresh', scaleContainers);
  ScrollTrigger.refresh();
});
