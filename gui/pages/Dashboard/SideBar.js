import React, {useState} from 'react';
import Image from 'next/image';
import styles from './Dashboard.module.css';

export default function SideBar({onSelectEvent}) {
  const [sectionSelected, setSelection] = useState('');

  const handleClick = (value) => {
    setSelection(value);
    onSelectEvent(value);
  };

  function twitterOauth(){
    const consumer_key = 'VEpWdkJqUllDNG9sRlNyaVdneWc6MTpjaQ';
    const scope = 'tweet.read%20tweet.write%20users.read%20offline.access' 
    // const scope = ['tweet.read', 'tweet.write', 'users.read', 'offline.access'];
    const redirect_uri = 'http://localhost:3000/api/oauth-twitter';
    const authUrl = `https://twitter.com/i/oauth2/authorize?response_type=code&client_id=${consumer_key}&redirect_uri=${redirect_uri}&scope=${scope}&state=state&code_challenge=challenge&code_challenge_method=plain`;
    console.log("AUTH URL : ",authUrl)
    window.location.href = authUrl;
  }

  const handleAuthenticateClick = async () => {
    twitterOauth()
  };

  return (
    <div className={styles.side_bar}>
      <div><Image width={64} height={48} className={styles.logo} src="/images/app-logo-light.png" alt="super-agi-logo"/>
      </div>
      <div className={styles.selection_section}>
        <div onClick={() => handleClick(sectionSelected !== 'agents' ? 'agents' : '')} className={`${styles.section} ${sectionSelected === 'agents' ? styles.selected : ''}`}>
          <div className={styles.button_icon}><Image width={17} height={17} src="/images/agents_light.svg" alt="agent-icon"/></div>
          <div>Agents</div>
        </div>
      </div>
      <div className={styles.selection_section}>
        <div onClick={() => handleClick(sectionSelected !== 'tools' ? 'tools' : '')} className={`${styles.section} ${sectionSelected === 'tools' ? styles.selected : ''}`}>
          <div className={styles.button_icon}><Image width={17} height={17} src="/images/tools_light.svg" alt="tools-icon"/></div>
          <div>Tools</div>
        </div>
      </div>
      <div className={styles.selection_section}>
       <div onClick={handleAuthenticateClick} className={`${styles.section} ${sectionSelected === 'agent_cluster' ? styles.selected : ''}`}>
         <div className={styles.button_icon}><Image width={17} height={17} src="/images/agent_cluster_light.svg" alt="agent-cluster-icon"/></div>
         <div>Twitter</div>
       </div>
      </div>
      {/*<div className={styles.selection_section}>*/}
      {/*  <div onClick={() => handleClick(sectionSelected !== 'apm' ? 'apm' : '')} className={`${styles.section} ${sectionSelected === 'apm' ? styles.selected : ''}`}>*/}
      {/*    <div className={styles.button_icon}><Image width={17} height={17} src="/images/apm_light.svg" alt="apm-icon"/></div>*/}
      {/*    <div>APM</div>*/}
      {/*  </div>*/}
      {/*</div>*/}
      {/*<div className={styles.selection_section}>*/}
      {/*  <div onClick={() => handleClick(sectionSelected !== 'embeddings' ? 'embeddings' : '')} className={`${styles.section} ${sectionSelected === 'embeddings' ? styles.selected : ''}`}>*/}
      {/*    <div className={styles.button_icon}><Image width={17} height={17} src="/images/embedding_light.svg" alt="embedding-icon"/></div>*/}
      {/*    <div>Embeddings</div>*/}
      {/*  </div>*/}
      {/*</div>*/}
    </div>
  );
}
